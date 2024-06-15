from typing import List, Union
from quart import Quart, request, session
from quart_session import Session
import simplejson as json
import asyncio as asio
# from yasearch.storing.weaviate import Finder as StoreFinder
# from yasearch.running.retriever import API as RetrieverApi
# from yasearch.running.indexer import API as IndexerApi
# from yasearch.storing.dataset import API as DatasetApi
from loguru import logger
from yasearch.storing.rethink import IReDocStore
from smart_open import open
from pathlib import Path
from yasearch.api.vtt import proc_video
import os
import uuid




app = Quart(
    __name__,
    static_url_path="",
    static_folder=str(Path(os.getcwd()) / "yasearch" / "build" / "static"),
    template_folder=str(Path(os.getcwd()) / "yasearch" / "build"),
)
app.config["SESSION_TYPE"] = "redis"
Session(app)
@app.post("/searching")
async def search():
    data = await request.get_data(parse_form_data=True)
    data = data.decode("utf-8")
    data = json.loads(data)
    query = data.get("text", "").strip()

    await asyncio.run(IReDocStore.add_search(query))
    # Placeholder to retrieve all the document(s) from the indexing stage
    # logger.info(data)

    # store = StoreFinder.find(collection_name)
    # retriever = RetrieverApi.named(search_by, store=store)
    # session["query"] = query
    # response = retriever.retrieve_topk(queries=[query], top_k=top_k)
    # logger.info(response)
    #return json.dumps({"docs": response}, ensure_ascii=False).encode("utf-8")
    return 'ok'