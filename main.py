import os
from glob import glob
from fastapi import FastAPI
from twelvelabs import TwelveLabs
from twelvelabs.models.task import Task

from dotenv import load_dotenv

load_dotenv()


app = FastAPI()

client = TwelveLabs(api_key=os.getenv("TWELVELABS_API_KEY"))
TWELVE_OUTPUT = "./twelve_output/"


@app.get("/")
async def read_root():
    return {"message": "Hello, world!"}


# @app.get("/details/{subject}")  # subject is index (i.e. shopify, ios, etc.)
# async def summarize(subject: str = None):
#     if not subject:
#         return {"Error": "No title provided."}

#     videos = client.index.video.list(index.id)
#     for video in videos:
#         print(f"Generating text for {video.id}")

#         res = client.generate.gist(
#             video_id=video.id, types=["title", "topic", "hashtag"]
#         )
#         print(f"Title: {res.title}\nTopics={res.topics}\nHashtags={res.hashtags}")

#         res = client.generate.summarize(video_id=video.id, type="summary")
#         # print(f"Summary: {res.summary}")
#         with open(TWELVE_OUTPUT + f"/{subject}_summary.out", "w+") as f:
#             f.write(res.summary)

#         print("Chapters:")
#         res = client.generate.summarize(video_id=video.id, type="chapter")
#         for chapter in res.chapters:
#             with open(TWELVE_OUTPUT + f"/{subject}_chapter.out", "a+") as f:
#                 f.write(
#                     f"chapter_number={chapter.chapter_number} chapter_title={chapter.chapter_title} chapter_summary={chapter.chapter_summary} start={chapter.start} end={chapter.end}"
#                 )
#             # print(
#             #     f"  chapter_number={chapter.chapter_number} chapter_title={chapter.chapter_title} chapter_summary={chapter.chapter_summary} start={chapter.start} end={chapter.end}"
#             # )

#         # print("Highlights:")
#         # res = client.generate.summarize(video_id=video.id, type="highlight")
#         # for highlight in res.highlights:
#         #     with open(TWELVE_OUTPUT+f'/{subject}_highlights.out', 'a+') as f:
#         #         f.write(f'Highlight={highlight.highlight} start={highlight.start} end={highlight.end}')
#         #     print(
#         #         f"  Highlight={highlight.highlight} start={highlight.start} end={highlight.end}"
#         #     )

#         res = client.generate.text(
#             video_id=video.id,
#             prompt="Based on this video, I want to generate five keywords for SEO (Search Engine Optimization).",
#         )
#         with open(TWELVE_OUTPUT + f"/{subject}_chapter.out", "a+") as f:
#             f.write(f"Open-ended Text: {res.data}")
#         # print(f"Open-ended Text: {res.data}")


@app.get("/index/{index_name}")  # subject is index (i.e. shopify, ios, etc.)
async def get(index_name: str = None):
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


@app.get("/summary/{index_name}")  # subject is index (i.e. shopify, ios, etc.)
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
        with open(TWELVE_OUTPUT + f"/{index_name}_summary.out", "w+") as f:
            f.write(res.summary)
    return {"Success": f"Output written to {index_name}_summary.out"}


@app.get("/chapter/{index_name}")  # subject is index (i.e. shopify, ios, etc.)
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
            with open(TWELVE_OUTPUT + f"/{index_name}_chapter.out", "a+") as f:
                f.write(
                    f"chapter_number={chapter.chapter_number} chapter_title={chapter.chapter_title} chapter_summary={chapter.chapter_summary} start={chapter.start} end={chapter.end}"
                )
    return {"Success": f"Output written to {index_name}_chapter.out"}


@app.get("/highlight/{index_name}")  # subject is index (i.e. shopify, ios, etc.)
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
    #         with open(TWELVE_OUTPUT+f'/{subject}_highlights.out', 'a+') as f:
    #             f.write(f'Highlight={highlight.highlight} start={highlight.start} end={highlight.end}')
    #         print(
    #             f"  Highlight={highlight.highlight} start={highlight.start} end={highlight.end}"
    #         )

    return {"Error", "/highlight endpoint not implemented."}


@app.get("/query/{index_name}")  # index_name is index (i.e. shopify, ios, etc.)
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
    with open(TWELVE_OUTPUT + f"/{index_name}_prompt.out", "w+") as f:
        f.write(f"{res.data}")
    return {"Success": f"Output written to {index_name}_prompt.out"}
