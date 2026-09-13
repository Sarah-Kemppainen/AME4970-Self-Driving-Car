from Data import DataParser
from LLMInterface import LLMInterface

if __name__ == "__main__":
    data = DataParser()
    print(data.rawData)
    print(data.x)
    print(data.y[0])

    # How to call DataParser attributed

    # llm = LLMInterface()