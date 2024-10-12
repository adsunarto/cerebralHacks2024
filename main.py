import os
from glob import glob
from twelvelabs import TwelveLabs
from twelvelabs.models.task import Task

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
app = FastAPI()


@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "query": q}


@app.get("/details/{subject}")  # subject is index (i.e. shopify, ios, etc.)
async def summarize(subject: str = None):
    if not subject:
        return {"Error": "No title provided."}

    # The path to the directory containing the videos you wish to upload.
    VIDEO_PATH = f"./videos/{subject}/*.mp4"  # Example: "/videos/*.mp4

    client = TwelveLabs(api_key=os.getenv('TWELVELABS_API_KEY'))

    index = client.index.create(
        name=f"{subject}",
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

    videos = client.index.video.list(index.id)
    for video in videos:
        print(f"Generating text for {video.id}")

        res = client.generate.gist(
            video_id=video.id, types=["title", "topic", "hashtag"]
        )
        print(f"Title: {res.title}\nTopics={res.topics}\nHashtags={res.hashtags}")

        res = client.generate.summarize(video_id=video.id, type="summary")
        print(f"Summary: {res.summary}")

        print("Chapters:")
        res = client.generate.summarize(video_id=video.id, type="chapter")
        for chapter in res.chapters:
            print(
                f"  chapter_number={chapter.chapter_number} chapter_title={chapter.chapter_title} chapter_summary={chapter.chapter_summary} start={chapter.start} end={chapter.end}"
            )

        print("Highlights:")
        res = client.generate.summarize(video_id=video.id, type="highlight")
        for highlight in res.highlights:
            print(
                f"  Highlight={highlight.highlight} start={highlight.start} end={highlight.end}"
            )

        res = client.generate.text(
            video_id=video.id,
            prompt="Based on this video, I want to generate five keywords for SEO (Search Engine Optimization).",
        )
        print(f"Open-ended Text: {res.data}")
