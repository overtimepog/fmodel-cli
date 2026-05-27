"""CLI-Anything harness for FModel — agent-native UE4/UE5 game asset browser.

Parse PAK files, inspect .uasset Blueprints, extract game content from the terminal.
"""
import json
import os
import sys

import click

from fmodel_cli.core.pak_parser import PakParser
from fmodel_cli.core.asset_parser import inspect_asset
from fmodel_cli.core.blueprint_parser import analyze_blueprint_vars


@click.group(invoke_without_command=True)
@click.option("--json", "json_output", is_flag=True, help="Machine-readable JSON output")
@click.option("--project", "-p", "project_path", help="Path to PAK file or session JSON")
@click.pass_context
def cli(ctx, json_output, project_path):
    """FModel CLI — browse and extract Unreal Engine game assets."""
    ctx.ensure_object(dict)
    ctx.obj["json"] = json_output
    ctx.obj["project"] = project_path

    if ctx.invoked_subcommand is None:
        # Enter REPL
        from fmodel_cli.utils.repl_skin import ReplSkin

        skin = ReplSkin("fmodel", version="0.1.0")
        skin.print_banner()
        ctx.invoke(repl, project_path=project_path)


# ── PAK Commands ────────────────────────────────────────────


@cli.group()
def pak():
    """PAK archive operations."""


@pak.command("info")
@click.option("--path", required=True, help="Path to .pak file")
@click.pass_context
def pak_info(ctx, path):
    """Show PAK file metadata (version, index info, file count)."""
    parser = PakParser(path)
    footer = parser.read_footer()
    entries = parser.list_files()

    if ctx.obj["json"]:
        click.echo(
            json.dumps(
                {
                    "path": path,
                    "version": footer["version"],
                    "index_offset": footer["index_offset"],
                    "index_size": footer["index_size"],
                    "file_count": len(entries),
                    "footer_offset": footer["footer_offset"],
                },
                indent=2,
            )
        )
    else:
        click.echo(f"PAK: {path}")
        click.echo(f"  Version:      {footer['version']}")
        click.echo(f"  File count:   {len(entries)}")
        click.echo(f"  Index offset: {footer['index_offset']} ({footer['index_offset']:#x})")
        click.echo(f"  Index size:   {footer['index_size']:,} bytes")


@pak.command("list")
@click.option("--path", required=True, help="Path to .pak file")
@click.option("--filter", "pattern", default=None, help="Filter files by substring")
@click.option("--limit", default=50, help="Max files to show")
@click.pass_context
def pak_list(ctx, path, pattern, limit):
    """List files in a PAK archive."""
    parser = PakParser(path)
    entries = parser.list_files()

    if pattern:
        entries = [e for e in entries if pattern in e["name"]]

    if ctx.obj["json"]:
        click.echo(json.dumps(entries[:limit], indent=2))
    else:
        for entry in entries[:limit]:
            click.echo(
                f"  {entry['name']:80s}  "
                f"{entry['uncompressed_size']:>10,}B  "
                f"{'compressed' if entry['compression_method'] else 'stored'}"
            )
        if len(entries) > limit:
            click.echo(f"  ... and {len(entries) - limit} more")


@pak.command("extract")
@click.option("--path", required=True, help="Path to .pak file")
@click.option("--file", "filename", default=None, help="Extract specific file by PAK path")
@click.option("--filter", "pattern", default=None, help="Extract files matching pattern")
@click.option("--output", "-o", "output_dir", default=".", help="Output directory")
@click.pass_context
def pak_extract(ctx, path, filename, pattern, output_dir):
    """Extract files from a PAK archive."""
    parser = PakParser(path)

    if filename:
        data = parser.extract_file(filename)
        if data is None:
            click.echo(f"File not found: {filename}", err=True)
            sys.exit(1)
        out_path = os.path.join(output_dir, os.path.basename(filename))
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "wb") as f:
            f.write(data)
        if ctx.obj["json"]:
            click.echo(json.dumps({"extracted": out_path, "size": len(data)}))
        else:
            click.echo(f"Extracted: {out_path} ({len(data):,} bytes)")
    elif pattern:
        extracted = parser.extract_all(output_dir, filter_pattern=pattern)
        if ctx.obj["json"]:
            click.echo(json.dumps({"extracted": len(extracted), "files": extracted}))
        else:
            click.echo(f"Extracted {len(extracted)} files to {output_dir}")
    else:
        click.echo("Specify --file or --filter", err=True)
        sys.exit(1)


# ── Asset Commands ──────────────────────────────────────────


@cli.group()
def asset():
    """Asset inspection (.uasset/.uexp)."""


@asset.command("inspect")
@click.option("--file", "filepath", required=True, help="Path to .uasset file")
@click.pass_context
def asset_inspect(ctx, filepath):
    """Inspect a .uasset Blueprint/asset — list exports, strings, classes."""
    info = inspect_asset(filepath)

    if ctx.obj["json"]:
        click.echo(
            json.dumps(
                {
                    "file": filepath,
                    "file_size": info["file_size"],
                    "package_offset": info["package_offset"],
                    "export_count": len(info["exports"]),
                    "blueprint_classes": info["blueprint_classes"],
                    "string_count": info["string_count"],
                },
                indent=2,
            )
        )
    else:
        click.echo(f"Asset: {filepath}")
        click.echo(f"  Size: {info['file_size']:,} bytes")
        click.echo(f"  Package offset: {info['package_offset']}")
        click.echo(f"  Exports ({len(info['exports'])}):")
        for exp in info["exports"][:20]:
            click.echo(f"    {exp}")
        if len(info["exports"]) > 20:
            click.echo(f"    ... and {len(info['exports']) - 20} more")
        click.echo(f"\n  Blueprint classes ({len(info['blueprint_classes'])}):")
        for bc in info["blueprint_classes"]:
            click.echo(f"    {bc}")
        click.echo(f"\n  Readable strings: {info['string_count']}")


@asset.command("strings")
@click.option("--file", "filepath", required=True, help="Path to .uasset file")
@click.option("--filter", "pattern", default=None, help="Filter strings by substring")
@click.pass_context
def asset_strings(ctx, filepath, pattern):
    """Extract readable strings from a .uasset Blueprint."""
    info = inspect_asset(filepath)
    strings = info["strings"]

    if pattern:
        strings = [s for s in strings if pattern.lower() in s.lower()]

    if ctx.obj["json"]:
        click.echo(json.dumps(strings, indent=2))
    else:
        for s in strings[:100]:
            click.echo(f"  {s}")
        if len(strings) > 100:
            click.echo(f"  ... and {len(strings) - 100} more ({len(strings)} total)")


# ── Blueprint analysis ───────────────────────────────────────


@asset.group()
def blueprint():
    """Blueprint bytecode analysis."""


@blueprint.command("vars")
@click.option("--file", "filepath", required=True, help="Path to .uasset file")
@click.pass_context
def blueprint_vars(ctx, filepath):
    """Find variable comparisons in Blueprint bytecode.

    Extracts which integer values each variable is compared against.
    Useful for finding enum/Switch-on-Int case values.
    """
    result = analyze_blueprint_vars(filepath)

    if "error" in result:
        click.echo(result["error"], err=True)

    if ctx.obj["json"]:
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(f"Name table: {result['name_count']} entries")
        click.echo(f"\nVariable comparisons:")
        for name, vals in sorted(result["variables"].items()):
            click.echo(f"  {name}: {vals}")
        if result.get("bp_mappings"):
            click.echo(f"\nBP asset mappings (property initializations):")
            for path, vals in sorted(result["bp_mappings"].items()):
                # Extract just the asset name
                short = path.split("/")[-1]
                click.echo(f"  {short}: {vals}")


# ── REPL ─────────────────────────────────────────────────────


@cli.command()
@click.option("--project", "-p", "project_path", default=None)
@click.pass_context
def repl(ctx, project_path):
    """Interactive REPL mode (default)."""
    from fmodel_cli.utils.repl_skin import ReplSkin

    skin = ReplSkin("fmodel", version="0.1.0")

    commands = {
        "pak info": "Show PAK metadata",
        "pak list": "List PAK contents",
        "pak extract": "Extract files from PAK",
        "asset inspect": "Inspect .uasset file",
        "asset strings": "Extract strings from .uasset",
        "help": "Show this help",
        "exit": "Exit REPL",
    }

    skin.help(commands)

    pt_session = skin.create_prompt_session()
    while True:
        try:
            line = skin.get_input(pt_session, project_name=project_path)
        except (KeyboardInterrupt, EOFError):
            skin.print_goodbye()
            break

        if not line or line.strip() == "":
            continue

        args = line.strip().split()
        if args[0] == "exit":
            skin.print_goodbye()
            break
        if args[0] == "help":
            skin.help(commands)
            continue

        # Delegate to Click
        try:
            # Build arguments for Click
            click_args = args.copy()
            if ctx.obj.get("json"):
                click_args.insert(0, "--json")
            if project_path:
                click_args.extend(["--project", project_path])

            # Run through Click
            with click.Context(cli, obj=ctx.obj) as click_ctx:
                cli(click_args, standalone_mode=False)
        except SystemExit:
            pass
        except Exception as e:
            skin.error(str(e))


if __name__ == "__main__":
    cli()
