from Data import Data
from LLMInterface import LLMInterface

if __name__ == "__main__":
    data = Data()
    print(data.rawData)
    print(data.data)
    print(data.data['x_m'])

    # llm = LLMInterface()