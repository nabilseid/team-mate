from openai import OpenAI
client = OpenAI()

def generic_chat_completions(query):
  completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
      {"role": "system", "content": "You are an assistance to help students optimise their schedules, facilitate collaboration, and provide tailored support to enhance their learning experience and job readiness."},
      {"role": "user", "content": query}
    ]
  )

  return completion.choices[0].message.content