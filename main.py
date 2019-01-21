import progressbar
import asyncio
import argparse
import json
from helper import truncate_middle, sizeof_fmt
from registryclient import RegistryClient
from sanic import Sanic
from sanic import response

app = Sanic()

widgets=[ progressbar.DynamicMessage("image"), progressbar.Bar(), progressbar.Percentage(),' [', progressbar.Timer(), '] ' ]

sizes = dict()

@app.route("/repositories.json")
async def get_repositories(request):
    dictlist = []
    for repo, value in sizes.items():
        value.update(repo=repo)
        dictlist.append(value)
    return response.json({'data': dictlist})

def fetch(reg):
    repositories = list()
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(reg.retrieveRepositories(repositories))

    bar = progressbar.ProgressBar(maxval=len(repositories), widgets=widgets)
    count = 1
    
    for repo in repositories:
        tags = list()
        sizeDict = dict()
        loop.run_until_complete(reg.retrieveTagsForRepository(repo, tags))
        loop.run_until_complete(asyncio.gather(
            *(reg.retrieveSizeForTagAndRepository(repo, tag, sizeDict) for tag in tags)
            ))
        sizes[repo] = { 'tags' : len(tags), 'size': sum(sizeDict.values()) }
        bar.update(count, image="%s (%s)" % (truncate_middle(repo, 30), "{:03d}".format(len(tags))))
        count += 1

    bar.finish()
    print(json.dumps(sizes))

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--registry',help='Specify the URL of your docker registry (use protocol prefix like http or https)', required=True)
    parser.add_argument('--username', help='Specify Username', required=True)
    parser.add_argument('--password', help='Specify Password', required=True)
    parser.add_argument('--cacert', help='Path to your custom root CA', required=False)
    args=parser.parse_args()

    print("Welcome to the Registry Size Reader, I'll now retrieve the image repository sizes for %s" % args.registry)
    
    reg = RegistryClient(args.registry + "/v2", args.username, args.password, args.cacert)

    fetch(reg)

    app.static('/', './static/index.html')
    app.static('/vendor', './static/vendor')

    app.run(host="0.0.0.0", port=8000)
    
    