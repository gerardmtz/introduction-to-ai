import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich import box

# Configure UTF-8 encoding
if sys.platform == "win32":
    import os
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.downloaders.openverse_downloader import OpenverseDownloader

console = Console()

def main():
    # Print header
    header = Panel(
        "[bold cyan]🔽 OPENVERSE DOWNLOADER TEST[/bold cyan]\n\n"
        "[yellow]Testing image download functionality[/yellow]",
        box=box.DOUBLE,
        border_style="cyan"
    )
    console.print("\n")
    console.print(header)
    console.print("\n")
    
    # Configuration
    query = "orange cats"
    num_images = 10
    save_dir = "data/raw/test"
    
    # Show config
    console.print(f"[cyan]🔍 Query:[/cyan] [bold]{query}[/bold]")
    console.print(f"[cyan]📸 Images:[/cyan] [bold]{num_images}[/bold]")
    console.print(f"[cyan]📁 Directory:[/cyan] [bold]{save_dir}[/bold]\n")
    
    # Download
    try:
        downloader = OpenverseDownloader()
        
        with console.status("[bold green]Downloading images...", spinner="dots"):
            downloaded_files = downloader.download_dataset(
                query=query,
                num_images=num_images,
                save_dir=save_dir
            )
        
        # Results
        result_panel = Panel(
            f"[bold green]✅ Success![/bold green]\n\n"
            f"[cyan]Downloaded:[/cyan] [bold]{len(downloaded_files)}[/bold] images\n"
            f"[cyan]Location:[/cyan] [bold]{Path(save_dir).absolute()}[/bold]",
            title="[bold green]Results[/bold green]",
            box=box.ROUNDED,
            border_style="green"
        )
        console.print("\n")
        console.print(result_panel)
        console.print("\n")
        
    except Exception as e:
        error_panel = Panel(
            f"[bold red]Error:[/bold red] {str(e)}",
            title="[bold red]❌ Failed[/bold red]",
            box=box.HEAVY,
            border_style="red"
        )
        console.print("\n")
        console.print(error_panel)
        console.print("\n")

if __name__ == "__main__":
    main()