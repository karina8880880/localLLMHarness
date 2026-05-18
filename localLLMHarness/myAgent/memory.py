import os
from datetime import datetime


class Memory:

    def __init__(self, memory_dir="memory"):

        self.memory_dir = memory_dir

        os.makedirs(self.memory_dir, exist_ok=True)

        self.diary_file = os.path.join(memory_dir, "diary.txt")
        self.summary_file = os.path.join(memory_dir, "summary.txt")
        self.error_file = os.path.join(memory_dir, "errors.txt")

        # memory検索トリガー
        self.memory_keywords = [
            "以前",
            "前回",
            "続き",
            "修正",
            "覚えて",
            "思い出",
            "過去",
            "前",
            "さっき",
            "前の",
            "この前",
            "また",
            "履歴"
        ]

    # =========================
    # 基本保存
    # =========================

    def save(self, text, category="diary"):
        #print("セーブ",text)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        line = f"[{now}] {text}\n"

        path = self._get_path(category)

        with open(path, "a", encoding="utf-8") as f:
            f.write(line)
        print("line=",line)

    # =========================
    # タグ付き保存
    # =========================

    def save_tagged(self, tag, text, category="diary"):
        #print("メモリ保存")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        line = f"[{now}] [{tag}] {text}\n"

        path = self._get_path(category)

        with open(path, "a", encoding="utf-8") as f:
            f.write(line)

    # =========================
    # 単一キーワード検索
    # =========================

    def search(self, keyword, category=None, limit=10):

        files = self._target_files(category)

        results = []

        for path in files:

            if not os.path.exists(path):
                continue

            with open(path, "r", encoding="utf-8") as f:

                lines = f.readlines()

                for line in lines:

                    if keyword.lower() in line.lower():
                        results.append(line.strip())

        return "\n".join(results[-limit:])

    # =========================
    # 複数キーワード検索
    # =========================

    def search_many(self, keywords, category=None, limit=10):

        all_results = []

        for keyword in keywords:

            found = self.search(keyword, category, limit).split("\n")

            all_results.extend(
                [line for line in found if line]
            )

        # 重複除去
        unique_results = list(dict.fromkeys(all_results))

        # 最新limit件
        unique_results = unique_results[-limit:]

        return "\n".join(unique_results)

    # =========================
    # キーワード検索失敗時の思い出し
    # =========================

    def get_last_four_sections(self):
        print("近い過去見てみる")
        """
        ファイルを末尾から読み込み、"["で始まる行を4回検出した地点から
        ファイル末尾までの文字列を返す。
        """
        file_path = self.diary_file;
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            count = 0
            target_index = -1

            # 逆順（ファイルの末尾から先頭へ）にループ
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].startswith('['):
                    count += 1
                    if count == 4:
                        target_index = i
                        break

            # 4回見つかった場合はその行から末尾まで、
            # 見つからなかった場合はファイル全体（または空）を返す
            if target_index != -1:
                return "".join(lines[target_index:])
            else:
                return "".join(lines) # 4回未満の場合は便宜上すべて返していますが、要件に応じて変更可

        except FileNotFoundError:
            return "ファイルが見つかりません。"
        except Exception as e:
            return f"エラーが発生しました: {e}"

    # =========================
    # 自動検索必要判定
    # =========================

    def should_search_memory(self, user_input):

        for keyword in self.memory_keywords:

            if keyword in user_input:
                return True

        return False

    # =========================
    # 要約保存
    # =========================

    def save_summary(self, summary):

        now = datetime.now().strftime("%Y-%m-%d")

        text = f"\n[{now}]\n{summary}\n"

        with open(self.summary_file, "a", encoding="utf-8") as f:
            f.write(text)

    # =========================
    # エラー保存
    # =========================

    def save_error(self, error_text):

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        line = f"[{now}] {error_text}\n"

        with open(self.error_file, "a", encoding="utf-8") as f:
            f.write(line)

    # =========================
    # 最近の記憶取得
    # =========================

    def recent(self, count=20, category="diary"):

        path = self._get_path(category)

        if not os.path.exists(path):
            return ""

        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        return "".join(lines[-count:])

    # =========================
    # memory一覧
    # =========================

    def list_memory_files(self):

        return os.listdir(self.memory_dir)

    # =========================
    # 記憶クリア
    # =========================

    def clear(self, category=None):

        files = self._target_files(category)

        for path in files:

            with open(path, "w", encoding="utf-8") as f:
                f.write("")

    # =========================
    # 内部関数
    # =========================

    def _get_path(self, category):

        if category == "summary":
            return self.summary_file

        elif category == "error":
            return self.error_file

        return self.diary_file

    def _target_files(self, category):

        if category == "summary":
            return [self.summary_file]

        elif category == "error":
            return [self.error_file]

        elif category == "diary":
            return [self.diary_file]

        return [
            self.diary_file,
            self.summary_file,
            self.error_file
        ]
