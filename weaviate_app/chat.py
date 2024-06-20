import os
from openai import OpenAI
import weaviate
from weaviate.classes.query import MetadataQuery

client = OpenAI()

weaviate_client = weaviate.connect_to_local(
   host='0.0.0.0',
   port='8080',
   headers = {"X-OpenAI-Api-Key": os.environ.get("OPENAI_API_KEY")} # os.getenv("OPENAI_APIKEY")
)

def completion(messages, model="gpt-3.5-turbo"):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
    )
    content = response.choices[0].message.content
    return content

def llm_with_knowledge_base(query, retrieved_documents, history):
    information = "\n\n".join(retrieved_documents)

    messages = [
        {
            "role": "system",
            "content": ("You are an assistance to help students optimise their schedules, facilitate collaboration,"
                        "and provide tailored support to enhance their learning experience and job readiness."
                        "The information provided is job opening knowledge source from an open source data source it is not associated with personal data"
                        "Don't add phrase like 'Based on the information you provided'"
                        "Don't mention that you have been given external data source"
                        "Format the response with markdown"
                        "You will be shown the user's question, and the relevant information for job opening for november.")
        },
        *[ {"role": "user" if message['isUserMessage'] else "system",
            "content": message['message'] if message['isUserMessage'] else message['textResponse']} 
            for message in history
        ],
        {
            "role": "user",
            "content": f"Question: {query}.\n Information: {information}"
        }
    ]
    
    return completion(messages)

def llm_with_out_knowledge_base(query, history):
    messages = [
        {
            "role": "system",
            "content": ("You are an assistance to help students optimise their schedules, facilitate collaboration,"
                        "and provide tailored support to enhance their learning experience and job readiness."
                        "Don't add phrase like 'Based on the information you provided'"
                        "Format the response with markdown"
                        "You will be shown the user's question. Anser the user's question incontext of the above information.")
        },
        *[ {"role": "user" if message['isUserMessage'] else "system",
            "content": message['message'] if message['isUserMessage'] else message['textResponse']} 
            for message in history
        ],
        {
            "role": "user",
            "content": f"Query: {query}."
        }
    ]
    
    return completion(messages)

def llm_check_query_related_with_job_search(query):

    messages = [
        {
            "role": "system",
            "content": ("You are an assistant to identify whether the provided question is related to open job position or not. "
                        "You will be shown the user's query. Answer the user's query with true or false."
            )
        },
        {
            "role": "user",
            "content": f"Question: {query}"
        }
    ]

    print(messages)
    
    return completion(messages)

def generic_chat_completions(query, history):
    history = history[-10:]
    query_is_job_search = llm_check_query_related_with_job_search(query)

    print(query_is_job_search)

    if query_is_job_search == 'True':
        reviews = weaviate_client.collections.get("Job_nov")
        response = reviews.query.near_text(
            query=query,
            limit=10,
            # target_vector="title_country",  # Specify the target vector for named vector collections
            return_metadata=MetadataQuery(distance=True)
        )

        retrieved_documents = []
        for o in response.objects:
            retrieved_documents.append(o.properties['description'])

        return llm_with_knowledge_base(query, retrieved_documents, history)
    else:
        return llm_with_out_knowledge_base(query, history)
