from myAgent import Agent, LLM, Tools, Memory, State

def main():
    llm = LLM()
    tools = Tools()
    memory = Memory()
    state = State()

    agent = Agent(llm, tools, memory, state)

    while True:
        user = input(">>> ")

        if user == "exit":
            break

        result = agent.run(user)
        print(result)

if __name__ == "__main__":
    main()
