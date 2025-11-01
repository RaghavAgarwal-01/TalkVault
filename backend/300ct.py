from datasets import load_dataset

ds = load_dataset("edinburghcstr/ami", "headset-single")
audio_sample = ds["train"][0]["audio"]["path"]
print(audio_sample)
