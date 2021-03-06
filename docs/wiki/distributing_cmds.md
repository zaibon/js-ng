# entry-points

Instead of manually copying helper scripts let's use entry_point for things like jshell, synctool, etc. these can be managed using entrypoints console_script entry https://packaging.python.org/specifications/entry-points/ and utilize `tool.poetry.scripts` to ship them


# poetry.scripts section
```
[tool.poetry.scripts]
jsng = "jumpscale.entry_points.jsng:run"
jsctl = "jumpscale.entry_points.jsctl:cli"

```


## Example (jsync tool)

### Write script
first write your entry point script in `entry_points` directory

```python
import click
from jumpscale.loader import j


@click.command()
def list_ssh_clients():
    # TODO: show terminal table with host information
    return print(j.clients.sshclient.list_all())


# jsync --clients "xmonader,client2" --paths "/home/xmonader/wspace/tq:/tmp/tq,..."
@click.command()
@click.option("--clients")
@click.option("--paths")
@click.option("--nosync", is_flag=True, default=False, type=bool)
def sync(clients, paths, nosync=False):
    clients = [cl_name.strip() for cl_name in clients.split(",")]
    paths_dict = {}
    for watched_path_info in paths.split(","):
        parts = watched_path_info.split(":")
        if len(parts) == 1:
            src, dest = parts[0], parts[0]
        else:
            src, dest = parts[0], parts[1]
        src = j.sals.fs.expanduser(src)
        paths_dict[src] = dest

    j.logger.info("clients: {}, paths {} ".format(clients, paths_dict))
    syncer = j.tools.syncer.Syncer(clients, paths_dict)
    syncer.start(sync=not nosync)


@click.group()
def cli():
    pass


cli.add_command(sync)
cli.add_command(list_ssh_clients)

if __name__ == "__main__":
    cli()

```

### Register it in pyproject.toml

Add it under `tool.poetry.scripts` section
```toml
[tool.poetry.scripts]
jsctl = "jumpscale.entry_points.jsctl:cli"
```
