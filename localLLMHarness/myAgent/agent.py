import json
import re

SYSTEM_PROMPT = """
You are an agent operating in a local environment.

Available tools:
- read_file(path): Read a file
- list_files(path): List files in a directory
- search_web(query): Search the web and get page contents
- write_file(path, content): Write a file
- execute_python_file(path): Execute a Python file
- run_command(cmd): Execute a safe command

Rules:
- Use tools only when necessary.
- You may output multiple JSON tool calls in one response.
- When using tools, output JSON only.
- Each tool call must have this format:
  { "tool": "search_web", "args": { "query": "AIとは" } }

- If all needed tools have been used, respond in plain text only.
- Do not include any explanation alongside tool JSON.
- Do not output <think> tags.
"""


class Agent:
    def __init__(self, llm, tools, memory, state):
        self.llm = llm
        self.tools = tools
        self.memory = memory
        self.state = state

    def clean_response(self, text):
        if not text:
            return ""

        # thinking 部分を除去
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = text.replace("<think>", "")
        text = text.replace("</think>", "")

        return text.strip()

    def extract_jsons(self, text):
        """
        LLM出力から複数のJSONオブジェクトを抽出する。
        """
        text = self.clean_response(text)

        results = []
        stack = []
        start = None

        for i, c in enumerate(text):
            if c == "{":
                if not stack:
                    start = i
                stack.append(c)

            elif c == "}":
                if stack:
                    stack.pop()

                    if not stack and start is not None:
                        candidate = text[start:i + 1]
                        try:
                            data = json.loads(candidate)
                            results.append(data)
                        except:
                            pass

        return results

    def execute_tool(self, tool, args):
        """
        ツール名に応じて実行する。
        """
        if tool == "list_files":
            return self.tools.list_files(args.get("path", "."))

        elif tool == "read_file":
            return self.tools.read_file(args.get("path", ""))

        elif tool == "run_command":
            return self.tools.run_command(args.get("cmd", ""))

        elif tool == "search_web":
            return self.tools.search_web(args.get("query", ""))

        elif tool == "write_file":
            return self.tools.write_file(
                args.get("path", ""),
                args.get("content", "")
            )

        elif tool == "execute_python_file":
            return self.tools.execute_python_file(args.get("path", ""))

        else:
            return "不明なツール"

    def run(self, user_input):
        context = f"ユーザーの要求:\n{user_input}\n"

        # state にも軽く残す
        try:
            self.state.current_goal = user_input
            self.state.step_count = 0
        except:
            pass

        # =========================
        # memory検索
        # =========================
        if self.memory.should_search_memory(user_input):
            #print("思い出してみる")

            keywords = [kw for kw in self.memory.memory_keywords if kw in user_input]
            if not keywords:
                keywords = [user_input]

            memory_result = self.memory.search_many(keywords)

            if memory_result:
                print("\n=== MEMORY ===")
                print(memory_result)
                context += f"\n過去の記憶:\n{memory_result}\n"
            else:
                context += "\n過去の記憶:\n" + self.memory.get_last_four_sections()
        else:
            print("思い出す必要はない")

        # =========================
        # agent loop
        # =========================
        last_tool_signature = None
        same_tool_count = 0

        for step in range(5):
            try:
                self.state.step_count = step
            except:
                pass

            prompt = SYSTEM_PROMPT + f"\n{context}"
            response = self.clean_response(self.llm.generate(prompt))

            print(f"\n--- STEP {step} ---")
            print("RAW:", response)

            datas = self.extract_jsons(response)

            # JSONが1つもないなら、そのまま最終回答とみなす
            if not datas:
                self.memory.save_tagged("response", response[:300])
                return response

            tool_executed = False
            plain_response = None

            for data in datas:
                if not isinstance(data, dict):
                    continue

                # ツール呼び出し
                if "tool" in data:
                    tool_executed = True
                    tool = data["tool"]
                    args = data.get("args", {})

                    # 同じツール連打の軽い抑制
                    tool_signature = f"{tool}:{json.dumps(args, ensure_ascii=False, sort_keys=True)}"
                    if tool_signature == last_tool_signature:
                        same_tool_count += 1
                    else:
                        same_tool_count = 0
                    last_tool_signature = tool_signature

                    if same_tool_count >= 2:
                        context += "\n同じツール呼び出しが続いたため、ここで停止して要約します。\n"
                        break

                    try:
                        result = self.execute_tool(tool, args)
                    except Exception as e:
                        result = str(e)
                        self.memory.save_error(result)

                    #print("TOOL RESULT:", result)

                    # memory保存
                    self.memory.save_tagged("tool", f"{tool}: {args}")
                    self.memory.save_tagged("tool_result", f"{tool}: {str(result)[:300]}")
                    #print("メモリ保存")

                    context += (
                        f"\n=== TOOL RESULT ===\n"
                        f"tool: {tool}\n"
                        f"args: {args}\n"
                        f"result:\n{result}\n"
                        f"===================\n"
                    )

                # ツールではないJSONで response がある場合
                elif "response" in data and isinstance(data["response"], str):
                    plain_response = data["response"]

            # ツールを使っていたなら次のループへ
            if tool_executed:
                continue

            # responseキー付きJSONならそれを返す
            if plain_response is not None:
                self.memory.save_tagged("response", plain_response[:300])
                return plain_response

            # JSONはあったが tool でも response でもない場合は、
            # 文字列としての最終回答に戻す
            self.memory.save_tagged("response", response[:300])
            return response

        # =========================
        # フォールバック
        # =========================
        final_prompt = f"""
あなたは優秀なアシスタントです。
以下の情報をもとに、ユーザーの質問に答えてください。

ユーザーの質問:
{user_input}

これまでの調査結果:
{context}

ツールは使わず、自然な文章で回答してください。
"""

        final_response = self.clean_response(self.llm.generate(final_prompt))
        self.memory.save_tagged("response", final_response[:300])
        return final_response
