import asyncio
import logging
import progressbar
import aiohttp

from rejson import Path
from helpers.helper import truncate_middle, sizeof_fmt
from helpers.constants import REPO_PREFIX

async def fetch(app):

    app.jobRunning = True

    loop = asyncio.get_event_loop()
    async with aiohttp.ClientSession(loop=loop) as session:
    
        repositories = await app.reg.retrieve_repositories(session)

        progress_queue = asyncio.Queue(loop=loop)
        for repo in repositories:
            progress_queue.put_nowait(repo)

        logging.info("Fetching the info for %d repositories", len(repositories))

        if app.cli:
            widgets=[ progressbar.DynamicMessage("image"), progressbar.Bar(),
                      progressbar.Percentage(),' [', progressbar.Timer(), '] ']
            app.bar = progressbar.ProgressBar(maxval=len(repositories), widgets=widgets)
            app.bar.start()
            app.count = 1
        
        async with aiohttp.ClientSession(loop=loop) as session:
            tasks = [(process_repository(app, session, progress_queue)) for repo in repositories]
            await asyncio.gather(*tasks)

        if app.cli:
            app.bar.finish()
            app.jobRunning = False
        else: 
            logging.info("Finished updating repositories.")

        app.jobRunning = False


async def process_repository(app, session, repo_queue):

    repo = await repo_queue.get()

    tags = await app.reg.retrieve_tags_for_repository(repo, session)
    tags_and_sizes = await asyncio.gather(*(app.reg.retrieve_size_for_tag_and_repository(repo, tag, session)
                                            for tag in tags))
    sizes = dict()
    [sizes.update(s["sizes"]) for s in tags_and_sizes]
    total_size = sum(sizes.values())

    if app.persistent:  
        app.db.jsonset(REPO_PREFIX + repo, Path.rootPath(), {'tags' : tags_and_sizes, 'size': total_size })
    else:
        app.db.update({repo: {'tags' : tags_and_sizes, 'size': total_size }})    

    if app.cli:
        app.bar.update(app.count, image="%s (%s)" % (truncate_middle(repo, 30), "{:03d}".format(len(tags))))
        app.count += 1
    else:
        logging.info("Updated repository with %s with %d tags (Total size: %s)",
                     repo, len(tags), sizeof_fmt(total_size))
                     