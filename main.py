import os
from glob import glob
from fastapi import FastAPI
import json
import requests

from twelvelabs import TwelveLabs
from twelvelabs.models.task import Task
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

client = TwelveLabs(api_key=os.getenv("TWELVELABS_API_KEY"))

KINDO_API_KEY = os.getenv("KINDO_API_KEY")


@app.get("/")
async def read_root():
    return {"message": "Hello, world!"}


@app.get("/index/{index_name}")
async def get(index_name: str):
    if not index_name:
        return {"Error": "No index_name provided."}

    # The path to the directory containing the videos you wish to upload.
    VIDEO_PATH = f"./videos/{index_name}/*.mp4"  # Example: "/videos/*.mp4

    index = client.index.create(
        name=f"{index_name}",
        engines=[
            {
                "name": "pegasus1.1",
                "options": ["visual", "conversation"],
            }
        ],
    )

    print(f"Created index: id={index.id} name={index.name} engines={index.engines}")

    video_files = glob(VIDEO_PATH)
    for video_file in video_files:
        print(f"Uploading {video_file}")
        task = client.task.create(index_id=index.id, file=video_file, language="en")
        print(f"Created task: id={task.id}")

        # (Optional) Monitor the video indexing process
        # Utility function to print the status of a video indexing task
        def on_task_update(task: Task):
            print(f"  Status={task.status}")

        task.wait_for_done(sleep_interval=50, callback=on_task_update)
        if task.status != "ready":
            raise RuntimeError(f"Indexing failed with status {task.status}")
        print(
            f"Uploaded {video_file}. The unique identifer of your video is {task.video_id}."
        )
    return {"Success": f"{index_name} indexed."}


@app.get("/summary/{index_name}")
async def summary(index_name: str):
    if not index_name:
        return {"Error": "No title provided."}

    index = client.index.list(
        name=f"{index_name}",
    )[0]

    videos = client.index.video.list(index.id)
    for video in videos:
        res = client.generate.summarize(video_id=video.id, type="summary")
        # print(f"Summary: {res.summary}")
        with open(f"./twelve_output/{index_name}_summary.out", "w+") as f:
            f.write(res.summary)
    return {"Success": f"Output written to {index_name}_summary.out"}


@app.get("/chapter/{index_name}")
async def chapter(index_name: str):
    if not index_name:
        return {"Error": "No title provided."}

    index = client.index.list(
        name=f"{index_name}",
    )[0]

    videos = client.index.video.list(index.id)
    for video in videos:
        res = client.generate.summarize(video_id=video.id, type="chapter")
        for chapter in res.chapters:
            with open(f"./twelve_output/{index_name}_chapter.out", "a+") as f:
                f.write(
                    f"chapter_number={chapter.chapter_number} chapter_title={chapter.chapter_title} chapter_summary={chapter.chapter_summary} start={chapter.start} end={chapter.end}"
                )
    return {"Success": f"Output written to {index_name}_chapter.out"}


@app.get("/highlight/{index_name}")
async def highlight(index_name: str):
    # if not index_name:
    #     return {"Error": "No title provided."}

    # index = client.index.list(
    #     name=f"{index_name}",
    # )[0]

    # videos = client.index.video.list(index.id)
    # for video in videos:
    #     res = client.generate.summarize(video_id=video.id, type="highlight")
    #     for highlight in res.highlights:
    #         with open(f"./twelve_output/{subject}_highlights.out', 'a+') as f:
    #             f.write(f'Highlight={highlight.highlight} start={highlight.start} end={highlight.end}')
    #         print(
    #             f"  Highlight={highlight.highlight} start={highlight.start} end={highlight.end}"
    #         )

    return {"Error", "/highlight endpoint not implemented."}


@app.get("/query/{index_name}")
async def query(index_name: str, prompt: str):
    if not prompt:
        return {"Error": "No prompt provided."}
    print("Prompt", prompt)

    index = client.index.list(
        name=f"{index_name}",
    )[0]

    videos = client.index.video.list(index.id)
    for video in videos:
        res = client.generate.text(
            video_id=video.id,
            prompt=f"{prompt}",
        )
    with open(f"./twelve_output/{index_name}_prompt.out", "w+") as f:
        f.write(f"{res.data}")
    return {"Success": f"Output written to {index_name}_prompt.out"}


@app.get("/summarize/{index_name}")
async def summarize(index_name: str, prompt: str):
    if not prompt:
        return {"Error": "No prompt provided."}
    print("Prompt", prompt)

    with open(f"./twelve_output/{index_name}_summary.out", "r") as f:
        summary = f.readlines()

    # Define the URL, headers, and data
    url = "https://llm.kindo.ai/v1/chat/completions"
    headers = {"api-key": f"{KINDO_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "watsonx/ibm/granite-13b-chat-v2",
        "messages": [
            {"role": "system", "content": f"{summary}"},
            {"role": "user", "content": f"{prompt}"},
        ],
    }

    # Send the request
    response = requests.post(
        url, headers=headers, json=data
    )  # Use 'json' for JSON data or 'data' for form-encoded

    # Check response status and content
    if response.status_code == 200:
        print("Request was successful!")
        print("Response data:", response.json())
        return response.json()["choices"][0]["message"]["content"]
    else:
        print(f"Request failed with status code {response.status_code}")
        print("Response content:", response.text)
        return response.text


# curl https: //llm.kindo.ai/v1/chat/completions \
#   -H "api-key: 2d3b28af-6f44-4e54-a696-8960ff71b25d-0d9cc35fcdcc1059" \
#   -H "content-type: application/json" \
#   -d '{
#     "model": "watsonx/ibm/granite-13b-chat-v2",
#     "messages": [
#         {
#             "role": "system",
#             "content": "Summary: The video provides a comprehensive sneak peek into the next generation of iOS, highlighting numerous new features and improvements. It begins with an announcement of the new iOS, followed by a quick succession of demonstrations showcasing the latest additions to the operating system. These include enhancements to the control center with options like Disconnect from Wi-Fi and Airplane Mode, and a new Unlock with Apple Watch feature on the lock screen. The home screen now includes an App Library for better app organization. Other notable updates include QuickTake and Volume Button Shutter in the camera app, a dynamic wallpaper option, and a Back Tap feature in settings. The health app introduces Sleep Tracking, and there are new functionalities in the messages app with Pinned Conversations. Family Setup, Guides in the maps app, and an enhanced Apple Arcade are also part of the update. Subscription services are streamlined with Apple One, and privacy settings are bolstered with new features. Accessibility receives attention with new tools, and the AirPods Max feature is introduced. The Home app, Safari, and Shortcuts also see improvements. The photos app now includes more robust editing capabilities, and the reminders and notes apps are updated for better usability. Weather, clock, files, music, and TV apps all receive enhancements. Additionally, theres a new Translate app, updated Memoji options, and more features in maps and messages. The mail, calendar, and photos memories apps are also updated. Screen Time, Find My, settings, notifications, wallpaper, and control center all receive new features. Dark Mode, Focus, Sleep, health, and fitness apps round out the extensive list of updates, culminating with a teaser that these features are Coming soon. Stay tuned. The video aims to inform and excite viewers about the forthcoming iOS updates, emphasizing Apples commitment to innovation and user experience."
#         },
#         {
#             "role": "user",
#             "content": "What went well during this demo? What can be improved? Provide your response in two sections with bullet points."
#         }
#     ]
# }'
