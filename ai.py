
import cohere

TOKEN = "TNGe72vCZtUtWB7csevGkedddxdXyp3mNttmoYUF"

def query_to_ai(prompt):
    co = cohere.ClientV2(TOKEN)

    response = co.chat(
        model="command-r-plus",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return dict(dict(dict(response)["message"])["content"][0])["text"]

if __name__ == "__main__":
    print(query_to_ai('''Imagine that you are a filter of foul language and insults.
    If there is something here that falls under bad words, please write 'Blocked', if not, write 'Active'.

    Comment to check:'''))

