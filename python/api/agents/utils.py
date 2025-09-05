def get_response(client, model_name, messages):
    response = client.chat.completions.create(
        messages=messages,
        model=model_name,
    ).choices[0].message.content
    return response
