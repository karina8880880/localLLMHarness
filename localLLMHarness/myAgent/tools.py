import subprocess
import os
import shlex

ALLOWED = ["ls", "pwd", "cat", "echo", "python3", "java"]
class Tools:

    def run_command(self, cmd):
        try:
            parts = shlex.split(cmd)

            if not parts:
                return "空コマンド"

            base = parts[0]

            if base not in ALLOWED:
                return "このコマンドは許可されていません"

            result = subprocess.check_output(
                parts,
                stderr=subprocess.STDOUT,
                timeout=30
            )

            return result.decode("utf-8")

        except Exception as e:
            return str(e)

    def read_file(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return str(e)

    def list_files(self, path="."):
        try:
            items = []

            for name in os.listdir(path):
                full = os.path.join(path, name)

                if os.path.isdir(full):
                    items.append(f"DIR: {name}")
                else:
                    items.append(f"FILE: {name}")

            return "\n".join(items)

        except Exception as e:
            return str(e)

    def write_file(self, path, content):
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            return f"{path} に書き込みました"

        except Exception as e:
            return str(e)

    def execute_java_file(self, file_path):
        """
        指定された既存のJavaファイルをコンパイルし、実行して出力を返す。
        """
        try:
            # ファイルの存在確認
            if not os.path.exists(file_path):
                return f"エラー: ファイル '{file_path}' が見つかりません。"

            if not file_path.endswith(".java"):
                return "エラー: 実行ツールには .java ファイルのパスを指定してください。"

            # 1. コンパイル (javac)
            try:
                subprocess.check_output(
                    ["javac", file_path],
                    stderr=subprocess.STDOUT,
                    timeout=30
                )
            except subprocess.CalledProcessError as e:
                return f"コンパイルエラー:\n{e.output.decode('utf-8')}"

            # 2. クラスパスとクラス名の特定
            # サブディレクトリにあるファイル (例: src/Main.java) にも対応できるようにする
            directory = os.path.dirname(file_path)
            if not directory:
                directory = "."
            
            # 拡張子を除いたファイル名をクラス名とする (Main.java -> Main)
            class_name = os.path.splitext(os.path.basename(file_path))[0]

            # 3. 実行 (java -cp <dir> <class>)
            try:
                result = subprocess.check_output(
                    ["java", "-cp", directory, class_name],
                    stderr=subprocess.STDOUT,
                    timeout=30
                )
                output = result.decode("utf-8")
                return output if output else "実行完了 (標準出力なし)"
            except subprocess.CalledProcessError as e:
                return f"実行時エラー:\n{e.output.decode('utf-8')}"

        except Exception as e:
            return f"システムエラー: {str(e)}"

        def execute_python_file(self, file_path):
            """
            指定された既存のPythonファイルを実行して出力を返す。
            """
            try:
                # ファイルの存在確認
                if not os.path.exists(file_path):
                    return f"エラー: ファイル '{file_path}' が見つかりません。"

                if not file_path.endswith(".py"):
                    return "エラー: 実行ツールには .py ファイルのパスを指定してください。"

                # 実行 (python3 <file_path>)
                try:
                    # 実行時のカレントディレクトリをスクリプトのあるディレクトリに合わせるかどうかの考慮
                    # 今回は呼び出し元のカレントディレクトリのまま実行します
                    result = subprocess.check_output(
                        ["python3", file_path],
                        stderr=subprocess.STDOUT,
                        timeout=30
                    )
                    output = result.decode("utf-8")
                    return output if output else "実行完了 (標準出力なし)"
                
                except subprocess.CalledProcessError as e:
                    # 構文エラー(SyntaxError)や実行時例外などはここでキャッチされます
                    return f"実行時エラー:\n{e.output.decode('utf-8')}"
                except subprocess.TimeoutExpired:
                    # LLMが無限ループするコードを書いた場合の安全策
                    return "エラー: 実行がタイムアウトしました（30秒）。無限ループの可能性があります。"

            except Exception as e:
                return f"システムエラー: {str(e)}"
