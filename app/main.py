import bottle
import requests


def get_kanye_quote():
    kanye_api = "https://api.kanye.rest/"
    content = requests.get(kanye_api).json()

    return content["quote"]


@bottle.route("/")
def hello():
    """Just say hello"""
    return bottle.template(
        "Hello!<br />Kanye says - <q>{{kanye_quote}}</q>", kanye_quote=get_kanye_quote()
    )


@bottle.route("/hello/<name>")
def named_hello(name):
    """say hello to name"""
    return bottle.template(
        "<b>Hello {{name}}</b>!<br />Kanye says - <q>{{kanye_quote}}</q>",
        name=name,
        kanye_quote=get_kanye_quote(),
    )


if __name__ == "__main__":
    bottle.run(host="localhost", port=8080)

app = bottle.default_app()
