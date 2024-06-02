import enum

class Models(enum.Enum):
    GPT3_5 = "gpt-3.5-turbo"
    GPT4 = "gpt-4-turbo"
    GPT4o = "gpt-4o"
    LLAMA3 = "llama3-70b-8192"
    MIXTRAL8_7 = "mixtral-8x7b-32768"
    MIXTRAL8_22 = 'mixtral-8x22b-65536'

anyscale_names = {
    Models.LLAMA3.value: "meta-llama/Meta-Llama-3-70B-Instruct",
    Models.MIXTRAL8_7.value: "mistralai/Mixtral-8x7B-Instruct-v0.1",
    Models.MIXTRAL8_22.value: "mistralai/Mixtral-8x22B-Instruct-v0.1"
}

# input names
model_mapping = {
    "gpt-3.5-turbo": Models.GPT3_5,
    "gpt-4-turbo": Models.GPT4,
    "gpt-4o": Models.GPT4o,
    "llama3": Models.LLAMA3,
    "mixtral8x7": Models.MIXTRAL8_7,
    "mixtral8x22": Models.MIXTRAL8_22
}