import typer

app = typer.Typer(
    name="habit",
    help="Terminal habit tracker with GitHub-style heatmaps.",
    no_args_is_help=True,
)


@app.callback(invoke_without_command=True)
def _callback(ctx: typer.Context) -> None:
    # Init DB on every invocation so first run is seamless.
    from habit_tracker.storage import init_db
    init_db()
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


# Commands will be registered in Phase C.
