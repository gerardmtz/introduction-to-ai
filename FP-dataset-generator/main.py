import argparse
import sys
import subprocess
from pathlib import Path
from types import SimpleNamespace
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn, TaskProgressColumn
from rich.align import Align
from rich import box
from rich.layout import Layout
from rich.text import Text
from rich.tree import Tree
from rich.columns import Columns
from rich.live import Live
import time
import os

# Configure UTF-8 encoding for Windows console
if sys.platform == "win32":
    import os
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stdin.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))
from src.pipeline import DatasetPipeline
# Importamos el nuevo agente
from src.ai_agent import AIAgent

console = Console()


def print_main_menu():
    """Print main menu with application selection"""
    banner_art = r"""
[bold cyan]
    ╔═══════════════════════════════════════════════════════════════════════╗
    ║                                                                       ║
    ║       █████╗ ██╗    ████████╗ ██████╗  ██████╗ ██╗     ███████╗     ║
    ║      ██╔══██╗██║    ╚══██╔══╝██╔═══██╗██╔═══██╗██║     ██╔════╝     ║
    ║      ███████║██║       ██║   ██║   ██║██║   ██║██║     ███████╗     ║
    ║      ██╔══██║██║       ██║   ██║   ██║██║   ██║██║     ╚════██║     ║
    ║      ██║  ██║██║       ██║   ╚██████╔╝╚██████╔╝███████╗███████║     ║
    ║      ╚═╝  ╚═╝╚═╝       ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝╚══════╝     ║
    ║                                                                       ║
    ║                    [bold yellow]🎨 AI TOOLS SUITE 🎨[/bold yellow]                           ║
    ║                                                                       ║
    ║                  [dim italic]Select Your Application[/dim italic]                         ║
    ║                                                                       ║
    ╚═══════════════════════════════════════════════════════════════════════╝
[/bold cyan]"""
    
    console.clear()
    console.print(Align.center(banner_art))
    console.print()


def show_application_menu():
    """Show menu to select application"""
    print_main_menu()
    
    # Create menu table
    menu_table = Table(
        box=box.HEAVY_EDGE,
        show_header=False,
        border_style="cyan",
        padding=(1, 3),
        title="[bold yellow]📱 Available Applications[/bold yellow]",
        title_style="bold yellow"
    )
    
    menu_table.add_column("Option", style="bold cyan", width=10, justify="center")
    menu_table.add_column("Application", style="bold white", width=35)
    menu_table.add_column("Description", style="dim white", width=40)
    
    menu_table.add_row(
        "[bold yellow]1[/bold yellow]",
        "🎨 [green]Dataset Generator[/green]",
        "[dim]Create ML datasets from web images[/dim]"
    )
    menu_table.add_row(
        "[bold yellow]2[/bold yellow]",
        "🕷️  [blue]Web Crawler AI[/blue]",
        "[dim]Launch web crawler with custom search[/dim]"
    )
    menu_table.add_row(
        "[bold yellow]3[/bold yellow]",
        "🤖 [magenta]AI Assistant[/magenta]",
        "[dim]Chat with the tools (Requires OpenAI Key)[/dim]"
    )
    menu_table.add_row(
        "[bold red]4[/bold red]",
        "❌ [red]Exit[/red]",
        "[dim]Close the application[/dim]"
    )
    
    console.print(Align.center(menu_table))
    console.print()
    
    # Get user choice
    choice_panel = Panel(
        "[yellow]Enter the number of your choice[/yellow]\n"
        "[dim]Press 1, 2, 3, or 4[/dim]",
        title="[bold cyan]⌨️  Your Selection[/bold cyan]",
        border_style="cyan",
        box=box.ROUNDED
    )
    console.print(Align.center(choice_panel))
    console.print()
    
    choice = Prompt.ask(
        "[bold cyan]Select application[/bold cyan]",
        choices=["1", "2", "3", "4"],
        default="1"
    )
    
    return choice


def launch_web_crawler(auto_config=None):
    """Launch web crawler with parameters"""
    console.print()
    console.rule("[bold blue]🕷️  Web Crawler AI Launcher[/bold blue]", style="blue")
    console.print()
    
    exe_file = None
    
    # 1. Determinar ejecutable (Automático si viene de IA, Manual si no)
    if auto_config:
        # Buscar el ejecutable en las ubicaciones correctas
        possible_paths = [
            Path("webcrawler-source/webcrawler"),  # macOS/Linux
            Path("webcrawler-source/webcrawler.exe"),  # Windows
            Path("webcrawler"),  # Si está en la raíz
            Path("webcrawler.exe"),  # Windows en raíz
        ]
        
        for path in possible_paths:
            if path.exists():
                exe_file = path.absolute()
                console.print(f"[green]✓ Found web crawler at:[/green] {exe_file}")
                break
        
        if not exe_file:
            console.print("[red]❌ Could not find web crawler executable automatically.[/red]")
            console.print("[yellow]Expected location: webcrawler-source/webcrawler[/yellow]")
            console.print("[dim]Tip: Make sure you ran the build step in run_project.sh[/dim]")
            return False
            
    if not exe_file:
        # Ask for executable path
        exe_panel = Panel(
            "[yellow]Enter the path to webcrawler executable[/yellow]\n\n"
            "[dim]Tip: You can drag and drop the file here[/dim]\n"
            "[dim]Default location: webcrawler-source/webcrawler[/dim]",
            title="[blue]📂 Executable Path[/blue]",
            border_style="blue",
            box=box.ROUNDED
        )
        console.print(exe_panel)
        console.print()
        
        exe_path = Prompt.ask(
            "[bold blue]Executable path[/bold blue]",
            default="webcrawler-source/webcrawler"
        )
        
        # Clean up the path
        exe_path = exe_path.strip().strip('"').strip("'")
        exe_file = Path(exe_path)
    
    # Validate file exists
    if not exe_file.exists():
        error_panel = Panel(
            f"[bold red]File not found:[/bold red]\n\n"
            f"[yellow]Path:[/yellow] {exe_file}\n"
            f"[yellow]Absolute path:[/yellow] {exe_file.absolute()}\n\n"
            f"[yellow]💡 Suggestions:[/yellow]\n"
            f"  • Check if the path is correct\n"
            f"  • Make sure you compiled the Go project\n"
            f"  • Run: cd webcrawler-source && go build -o webcrawler .\n"
            f"  • Verify the file exists at: webcrawler-source/webcrawler\n",
            title="[bold red]❌ ERROR[/bold red]",
            border_style="red",
            box=box.HEAVY
        )
        console.print()
        console.print(error_panel)
        console.print()
        
        if not auto_config and Confirm.ask("\n[yellow]Try again?[/yellow]", default=True):
            return launch_web_crawler()
        else:
            return False
    
    # 2. Configurar parámetros
    if auto_config:
        keyword = auto_config.get('keyword')
        num_pages = auto_config.get('num_pages', 5)
        verbose = True
        console.print(f"[cyan]🤖 Auto-configuring crawler for:[/cyan] [green]{keyword}[/green]")
    else:
        # Get search parameters interactively
        console.print()
        console.rule("[bold cyan]🔧 Configuration[/bold cyan]", style="cyan")
        
        params_panel = Panel(
            "[cyan]Configure the web crawler parameters[/cyan]\n\n"
            "[dim]The crawler will search for your query and scrape pages[/dim]",
            title="[cyan]⚙️  Parameters[/cyan]",
            border_style="cyan",
            box=box.ROUNDED
        )
        console.print(params_panel)
        console.print()
        
        # Get search keyword
        keyword = ""
        while not keyword:
            keyword = Prompt.ask(
                "[bold cyan]🔍 Search keyword (-k)[/bold cyan]",
                default="artificial intelligence"
            ).strip()
            if not keyword:
                console.print("[red]❌ Keyword cannot be empty![/red]")
        
        # Get number of pages
        num_pages = IntPrompt.ask(
            "[bold cyan]📄 Number of pages to crawl (-p)[/bold cyan]",
            default=5
        )
        
        # Verbose mode
        verbose = Confirm.ask(
            "[bold cyan]📊 Enable verbose mode (-v)?[/bold cyan]",
            default=True
        )
    
    # Build command
    command_parts = [f'"{exe_file.absolute()}"']
    command_parts.append(f'-k "{keyword}"')
    if verbose:
        command_parts.append('-v')
    command_parts.append(f'-p {num_pages}')
    
    full_command = ' '.join(command_parts)
    
    # Show configuration summary only if manual
    if not auto_config:
        console.print()
        console.rule("[bold yellow]📋 Summary[/bold yellow]", style="yellow")
        console.print()
        
        config_table = Table(
            box=box.ROUNDED,
            show_header=False,
            border_style="cyan",
            padding=(0, 2)
        )
        
        config_table.add_column("Parameter", style="bold cyan", width=25)
        config_table.add_column("Value", style="bold white", width=50)
        
        config_table.add_row("📂 Executable", exe_file.name)
        config_table.add_row("📍 Location", str(exe_file.parent))
        config_table.add_row("🔍 Search Keyword", f"[green]{keyword}[/green]")
        config_table.add_row("📄 Pages to Crawl", f"[yellow]{num_pages}[/yellow]")
        config_table.add_row("📊 Verbose Mode", "[green]✅ Enabled[/green]" if verbose else "[red]❌ Disabled[/red]")
        config_table.add_row("⚙️  Full Command", f"[dim]{full_command}[/dim]")
        
        console.print(Align.center(config_table))
        console.print()
        
        # Confirm launch
        confirm_panel = Panel(
            "[yellow]Review the configuration above[/yellow]\n"
            "[dim]The crawler will start in a new window[/dim]",
            title="[bold yellow]⚠️  Confirmation[/bold yellow]",
            border_style="yellow",
            box=box.ROUNDED
        )
        console.print(confirm_panel)
        
        if not Confirm.ask("\n[bold yellow]🚀 Launch web crawler?[/bold yellow]", default=True):
            console.print("[yellow]⚠️  Launch cancelled[/yellow]\n")
            return False
    else:
        console.print(f"[dim]Command: {full_command}[/dim]")

    # Launch the crawler
    try:
        console.print()
        with console.status("[bold green]🚀 Launching web crawler...", spinner="dots"):
            time.sleep(0.5)
        
        console.print("[green]✓[/green] Launching web crawler...\n")
        
        # Working directory
        working_dir = exe_file.parent
        
        # Launch process with parameters
        if sys.platform == "win32":
            # Windows: Nueva ventana de consola
            process = subprocess.Popen(
                full_command,
                shell=True,
                cwd=str(working_dir),
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        elif sys.platform == "darwin":
            # macOS: Usar Terminal.app
            apple_script = f'''
            tell application "Terminal"
                do script "cd '{working_dir}' && '{exe_file.absolute()}' -k '{keyword}' -p {num_pages} {'-v' if verbose else ''}"
                activate
            end tell
            '''
            process = subprocess.Popen(['osascript', '-e', apple_script])
        else:
            # Linux: Terminal normal
            process = subprocess.Popen(
                [str(exe_file.absolute()), '-k', keyword, '-p', str(num_pages)] + (['-v'] if verbose else []),
                cwd=str(working_dir)
            )
        
        # Give it a moment to start
        time.sleep(1)
        
        # Check if process is still running
        poll = process.poll()
        if poll is not None and poll != 0:
            error_panel = Panel(
                f"[bold red]Application failed to start:[/bold red]\n\n"
                f"[yellow]Exit code:[/yellow] {poll}\n\n"
                f"[yellow]💡 Suggestions:[/yellow]\n"
                f"  • Check if the executable is valid\n"
                f"  • Try running as administrator\n"
                f"  • Verify all dependencies are installed\n",
                title="[bold red]❌ ERROR[/bold red]",
                border_style="red",
                box=box.HEAVY
            )
            console.print()
            console.print(error_panel)
            console.print()
            return False
        
        if not auto_config:
            success_panel = Panel(
                "[bold green]✅ Web Crawler launched successfully![/bold green]\n\n"
                f"[cyan]Process ID:[/cyan] {process.pid}\n"
                f"[cyan]Working Directory:[/cyan] {working_dir}\n"
                f"[cyan]Search Query:[/cyan] {keyword}\n"
                f"[cyan]Pages to Crawl:[/cyan] {num_pages}\n\n"
                "[dim]The crawler is running in a separate console window[/dim]\n"
                "[dim]Check the new window for progress and results[/dim]",
                title="[bold green]🎉 Success[/bold green]",
                border_style="green",
                box=box.DOUBLE
            )
            console.print(success_panel)
            console.print()
        
        # Ask if wait for process (if manual) or wait automatically (if AI)
        wait = auto_config is not None  # Default true for AI
        if not auto_config:
            wait = Confirm.ask("[yellow]Wait for crawler to finish?[/yellow]", default=False)

        if wait:
            with console.status("[bold yellow]Waiting for crawler to complete...", spinner="dots"):
                process.wait()
            
            exit_code = process.returncode
            if exit_code == 0:
                console.print("[green]✓[/green] Crawler completed successfully\n")
            else:
                console.print(f"[yellow]⚠️  Crawler exited with code: {exit_code}[/yellow]\n")
        
        return True
        
    except PermissionError:
        error_panel = Panel(
            f"[bold red]Permission denied![/bold red]\n\n"
            f"[yellow]You don't have permission to run this file.[/yellow]\n\n"
            f"[yellow]💡 Solutions:[/yellow]\n"
            f"  • Run this program as administrator\n"
            f"  • Check file permissions\n"
            f"  • Make sure the file is not blocked\n",
            title="[bold red]❌ PERMISSION ERROR[/bold red]",
            border_style="red",
            box=box.HEAVY
        )
        console.print()
        console.print(error_panel)
        console.print()
        return False
        
    except Exception as e:
        error_panel = Panel(
            f"[bold red]Failed to launch crawler:[/bold red]\n\n{str(e)}\n\n"
            "[yellow]💡 Suggestions:[/yellow]\n"
            "  • Check if the file is executable\n"
            "  • Verify you have permissions\n"
            "  • Try running as administrator\n"
            "  • Make sure all dependencies are installed\n",
            title="[bold red]❌ ERROR[/bold red]",
            border_style="red",
            box=box.HEAVY
        )
        console.print()
        console.print(error_panel)
        console.print()
        return False


def print_banner():
    """Print beautiful animated ASCII banner"""
    banner_art = r"""
[bold cyan]
    ╔═══════════════════════════════════════════════════════════════════════╗
    ║                                                                       ║
    ║     ██████╗  █████╗ ████████╗ █████╗ ███████╗███████╗████████╗      ║
    ║     ██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗██╔════╝██╔════╝╚══██╔══╝      ║
    ║     ██║  ██║███████║   ██║   ███████║███████╗█████╗     ██║         ║
    ║     ██║  ██║██╔══██║   ██║   ██╔══██║╚════██║██╔══╝     ██║         ║
    ║     ██████╔╝██║  ██║   ██║   ██║  ██║███████║███████╗   ██║         ║
    ║     ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚══════╝   ╚═╝         ║
    ║                                                                       ║
    ║                [bold yellow]🎨 IMAGE DATASET GENERATOR 🎨[/bold yellow]                      ║
    ║                                                                       ║
    ║              [dim italic]Automated ML Dataset Creation Tool[/dim italic]                  ║
    ║              [dim]Powered by Openverse & AI Magic[/dim]                       ║
    ║                                                                       ║
    ╚═══════════════════════════════════════════════════════════════════════╝
[/bold cyan]"""
    
    version_info = "[dim]v1.0.0 | Made with ❤️  for ML Engineers[/dim]"
    
    console.clear()
    console.print(Align.center(banner_art))
    console.print(Align.center(version_info))
    console.print()


def print_welcome_message():
    """Print welcome message with features"""
    features = Panel(
        "[bold cyan]✨ Features:[/bold cyan]\n\n"
        "  🔍 [green]Smart Image Search[/green] - Find images from Openverse\n"
        "  📸 [green]Batch Download[/green] - Download multiple images at once\n"
        "  🎨 [green]Auto Processing[/green] - Resize and optimize automatically\n"
        "  📊 [green]Dataset Splitting[/green] - Train/Val/Test split ready\n"
        "  📝 [green]Metadata Generation[/green] - Complete documentation\n"
        "  ⚡ [green]Fast & Efficient[/green] - Optimized for speed\n",
        title="[bold yellow]Welcome![/bold yellow]",
        border_style="cyan",
        box=box.ROUNDED,
        padding=(1, 2)
    )
    console.print(features)
    console.print()


def get_user_input():
    """Get configuration from user interactively with beautiful prompts"""
    
    print_banner()
    print_welcome_message()
    
    # Create a nice divider
    console.rule("[bold cyan]📝 Configuration[/bold cyan]", style="cyan")
    console.print()
    
    # Query with validation and suggestions
    query_panel = Panel(
        "[dim]Enter what you want to search for\n"
        "Examples: 'orange cats', 'red flowers', 'mountain landscapes'[/dim]",
        title="[cyan]💡 Tip[/cyan]",
        border_style="dim",
        box=box.SIMPLE
    )
    console.print(query_panel)
    
    query = ""
    while not query:
        query = Prompt.ask("\n[bold cyan]🔍 Search query[/bold cyan]", default="orange cats").strip()
        if not query:
            console.print("[red]❌ Query cannot be empty![/red]")
    
    console.print()
    
    # Number of images with visual guidance
    num_guide = Panel(
        "[dim]Recommended: 50-100 images for small datasets\n"
        "             500+ images for production models[/dim]",
        title="[cyan]💡 Tip[/cyan]",
        border_style="dim",
        box=box.SIMPLE
    )
    console.print(num_guide)
    
    num = IntPrompt.ask(
        "\n[bold cyan]📸 Number of images[/bold cyan]",
        default=50
    )
    
    console.print()
    
    # Dataset name
    name = Prompt.ask(
        "[bold cyan]📁 Dataset name[/bold cyan]",
        default=f"{query.title()} Dataset"
    )
    
    console.print()
    
    # Description
    description = Prompt.ask(
        "[bold cyan]📝 Description[/bold cyan] [dim](optional, press Enter to skip)[/dim]",
        default=""
    )
    
    console.print()
    console.rule("[bold magenta]⚙️  Advanced Settings[/bold magenta]", style="magenta")
    console.print()
    
    # Advanced settings with better explanation
    advanced_panel = Panel(
        "[yellow]Configure image size, quality, and other advanced options[/yellow]",
        title="[magenta]⚙️  Advanced Mode[/magenta]",
        border_style="magenta",
        box=box.SIMPLE
    )
    console.print(advanced_panel)
    
    advanced = Confirm.ask("\n[yellow]Would you like to configure advanced options?[/yellow]", default=False)
    
    console.print()
    
    if advanced:
        size = IntPrompt.ask("[cyan]📐 Image size (pixels)[/cyan]", default=256)
        quality = IntPrompt.ask("[cyan]✨ JPEG quality (1-100)[/cyan]", default=90)
        output = Prompt.ask("[cyan]📂 Output directory[/cyan]", default="data/processed")
        keep_temp = Confirm.ask("[cyan]🗂️  Keep temporary files?[/cyan]", default=False)
    else:
        size = 256
        quality = 90
        output = "data/processed"
        keep_temp = False
    
    return {
        'query': query,
        'num': num,
        'name': name,
        'description': description,
        'output': output,
        'size': size,
        'quality': quality,
        'train_ratio': 0.7,
        'val_ratio': 0.15,
        'test_ratio': 0.15,
        'seed': 42,
        'keep_temp': keep_temp,
        'min_size': 100
    }


def print_config(config):
    """Print configuration in a beautiful table with visual enhancements"""
    console.print()
    console.rule("[bold yellow]📋 Configuration Summary[/bold yellow]", style="yellow")
    console.print()
    
    # Main config table
    main_table = Table(
        box=box.DOUBLE_EDGE,
        show_header=True,
        header_style="bold magenta",
        border_style="cyan",
        title="[bold yellow]Dataset Configuration[/bold yellow]",
        title_style="bold yellow",
        padding=(0, 1)
    )
    
    main_table.add_column("Setting", style="bold cyan", width=28, no_wrap=True)
    main_table.add_column("Value", style="bold white", width=45)
    
    main_table.add_row("🔍 Search Query", f"[green]{config['query']}[/green]")
    main_table.add_row("📸 Images to Download", f"[green]{config['num']}[/green] images")
    main_table.add_row("📁 Dataset Name", f"[green]{config['name']}[/green]")
    main_table.add_row("📝 Description", config['description'] or "[dim italic](none)[/dim italic]")
    main_table.add_row("📂 Output Directory", f"[blue]{config['output']}[/blue]")
    
    # Technical settings table
    tech_table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold blue",
        border_style="blue",
        title="[bold blue]⚙️  Technical Settings[/bold blue]",
        title_style="bold blue",
        padding=(0, 1)
    )
    
    tech_table.add_column("Parameter", style="cyan", width=28)
    tech_table.add_column("Value", style="white", width=45)
    
    tech_table.add_row("📐 Image Size", f"[green]{config['size']} x {config['size']}[/green] pixels")
    tech_table.add_row("✨ JPEG Quality", f"[green]{config['quality']}%[/green]")
    tech_table.add_row("📏 Minimum Size", f"[yellow]{config['min_size']} x {config['min_size']}[/yellow] pixels")
    
    # Split ratios with progress bars
    train_bar = "█" * int(config['train_ratio'] * 20)
    val_bar = "█" * int(config['val_ratio'] * 20)
    test_bar = "█" * int(config['test_ratio'] * 20)
    
    split_text = (
        f"[green]Train: {config['train_ratio']*100:.0f}%[/green] {train_bar}\n"
        f"[yellow]Val:   {config['val_ratio']*100:.0f}%[/yellow] {val_bar}\n"
        f"[blue]Test:  {config['test_ratio']*100:.0f}%[/blue] {test_bar}"
    )
    
    tech_table.add_row("📊 Split Ratios", split_text)
    tech_table.add_row("🌱 Random Seed", f"[magenta]{config['seed']}[/magenta]")
    tech_table.add_row("🗂️  Keep Temp Files", "[green]✅ Yes[/green]" if config['keep_temp'] else "[red]❌ No[/red]")
    
    # Display tables
    console.print(Align.center(main_table))
    console.print()
    console.print(Align.center(tech_table))
    console.print()


def show_success(results, config):
    """Show success message with detailed stats and visual feedback"""
    console.print()
    console.rule("[bold green]✅ Success![/bold green]", style="green")
    console.print()
    
    # Create a tree for file structure
    file_tree = Tree(
        f"[bold cyan]📁 {config['output']}[/bold cyan]",
        guide_style="cyan"
    )
    
    dataset_branch = file_tree.add(f"[bold green]{config['name']}[/bold green]")
    dataset_branch.add(f"[yellow]📊 train/[/yellow] ({results.get('train_images', 0)} images)")
    dataset_branch.add(f"[yellow]📊 val/[/yellow] ({results.get('val_images', 0)} images)")
    dataset_branch.add(f"[yellow]📊 test/[/yellow] ({results.get('test_images', 0)} images)")
    dataset_branch.add("[blue]📄 dataset_info.json[/blue]")
    dataset_branch.add("[blue]📄 README.md[/blue]")
    
    # Stats table with visual elements
    stats_table = Table(
        box=box.DOUBLE,
        show_header=True,
        header_style="bold green",
        border_style="green",
        title="[bold green]📊 Dataset Statistics[/bold green]",
        padding=(0, 2)
    )
    
    stats_table.add_column("Metric", style="cyan", width=25)
    stats_table.add_column("Count", style="bold green", justify="center", width=15)
    stats_table.add_column("Percentage", style="yellow", justify="center", width=15)
    
    total = results.get('total_images', 0)
    train = results.get('train_images', 0)
    val = results.get('val_images', 0)
    test = results.get('test_images', 0)
    
    stats_table.add_row("📸 Total Images", f"{total}", "100%")
    stats_table.add_row("🎯 Training Set", f"{train}", f"{(train/total*100):.1f}%" if total > 0 else "0%")
    stats_table.add_row("✅ Validation Set", f"{val}", f"{(val/total*100):.1f}%" if total > 0 else "0%")
    stats_table.add_row("🧪 Test Set", f"{test}", f"{(test/total*100):.1f}%" if total > 0 else "0%")
    
    # Create columns layout
    console.print(Columns([stats_table, file_tree], equal=True, expand=True))
    console.print()
    
    # Success message with location
    success_panel = Panel(
        f"[bold green]🎉 Dataset generation completed successfully![/bold green]\n\n"
        f"[cyan]📁 Location:[/cyan] [bold]{results.get('output_dir', config['output'])}[/bold]\n"
        f"[cyan]⏱️  Time:[/cyan] [bold]{results.get('time_elapsed', 'N/A')}[/bold]\n\n"
        f"[dim]You can now use this dataset for training your ML models![/dim]",
        title="[bold green]✨ All Done![/bold green]",
        border_style="green",
        box=box.DOUBLE,
        padding=(1, 2)
    )
    
    console.print(success_panel)
    console.print()


def show_error(error_msg):
    """Show detailed error message with suggestions"""
    console.print()
    console.rule("[bold red]❌ Error Occurred[/bold red]", style="red")
    console.print()
    
    error_panel = Panel(
        f"[bold red]Error Details:[/bold red]\n\n"
        f"{error_msg}\n\n"
        f"[yellow]💡 Suggestions:[/yellow]\n"
        f"  • Check your internet connection\n"
        f"  • Verify the search query is valid\n"
        f"  • Try with fewer images\n"
        f"  • Check if you have write permissions\n",
        title="[bold red]❌ ERROR[/bold red]",
        border_style="red",
        box=box.HEAVY,
        padding=(1, 2)
    )
    console.print(error_panel)
    console.print()


def run_dataset_generator(args=None):
    """Run the dataset generator application"""
    try:
        if args and hasattr(args, 'query') and args.query and args.num and args.name:
            if not isinstance(args, SimpleNamespace): # Only print banner if not interactive
                 print_banner()
            
            config = {
                'query': args.query,
                'num': args.num,
                'name': args.name,
                'description': args.description,
                'output': args.output,
                'size': args.size,
                'quality': args.quality,
                'train_ratio': args.train_ratio,
                'val_ratio': args.val_ratio,
                'test_ratio': args.test_ratio,
                'seed': args.seed,
                'keep_temp': args.keep_temp,
                'min_size': args.min_size
            }
        else:
            config = get_user_input()
        
        # Show configuration
        print_config(config)
        
        # Confirm with styled prompt if not automated via args
        if not args or not hasattr(args, 'query'):
            confirm_panel = Panel(
                "[yellow]Review the configuration above.[/yellow]\n"
                "[dim]Press Enter to start or Ctrl+C to cancel[/dim]",
                title="[bold yellow]⚠️  Confirmation[/bold yellow]",
                border_style="yellow",
                box=box.ROUNDED
            )
            console.print(confirm_panel)
            
            if not Confirm.ask("\n[bold yellow]🚀 Start dataset generation?[/bold yellow]", default=True):
                console.print("\n[yellow]⚠️  Operation cancelled by user[/yellow]\n")
                return False
        
        console.print()
        console.rule("[bold green]🚀 Starting Pipeline[/bold green]", style="green")
        console.print()
        
        # Initialize with animation
        with console.status("[bold green]🔧 Initializing pipeline...", spinner="dots"):
            pipeline = DatasetPipeline(
                target_size=(config['size'], config['size']),
                min_size=(config['min_size'], config['min_size']),
                quality=config['quality'],
                train_ratio=config['train_ratio'],
                val_ratio=config['val_ratio'],
                test_ratio=config['test_ratio'],
                seed=config['seed']
            )
            time.sleep(1)
        
        console.print("[green]✓[/green] Pipeline initialized successfully\n")
        
        # Run pipeline
        start_time = time.time()
        
        results = pipeline.generate_dataset(
            query=config['query'],
            num_images=config['num'],
            dataset_name=config['name'],
            description=config['description'],
            output_base_dir=config['output'],
            keep_temp_files=config['keep_temp']
        )
        
        elapsed_time = time.time() - start_time
        results['time_elapsed'] = f"{elapsed_time:.2f}s"
        
        # Show results
        if results['success']:
            show_success(results, config)
            return True
        else:
            show_error(results.get('error', 'Unknown error'))
            return False
            
    except Exception as e:
        show_error(str(e))
        import traceback
        console.print("[dim]" + traceback.format_exc() + "[/dim]")
        return False


def run_ai_assistant():
    """Run the interactive AI assistant loop"""
    agent = AIAgent()
    
    console.clear()
    console.rule("[bold magenta]🤖 AI Assistant (GPT-Nano Integration)[/bold magenta]", style="magenta")
    console.print("\n[dim]I can help you generate datasets or crawl the web. Just ask![/dim]")
    console.print("[dim]Type 'exit' to return to menu.[/dim]\n")

    if not agent.is_configured():
        console.print(Panel("[red]OPENAI_API_KEY not found in environment variables.[/red]\nPlease configure your .env file.", title="Error", border_style="red"))
        Prompt.ask("Press Enter to continue")
        return

    while True:
        user_input = Prompt.ask("\n[bold magenta]You[/bold magenta]")
        
        if user_input.lower() in ['exit', 'quit', 'back']:
            break
            
        with console.status("[bold magenta]Thinking...", spinner="dots"):
            result = agent.parse_instruction(user_input)
            
        console.print(f"[dim]Debug - AI returned: {result}[/dim]")
            
        if "error" in result:
            console.print(f"[red]Error: {result['error']}[/red]")
            continue
            
        tool = result.get("tool")
        
        if tool == "chat":
            console.print(Panel(result["message"], title="[bold magenta]AI[/bold magenta]", border_style="magenta"))
            
        elif tool == "dataset_generator":
            console.print("[green]🤖 Creating dataset configuration from your request...[/green]")
            
            time.sleep(2)
            
            # Convert dict to Namespace object to simulate argparse args
            args_mock = SimpleNamespace(
                query=result.get('query'),
                num=result.get('num'),
                name=result.get('name'),
                description=f"Generated by AI via query: {result.get('query')}",
                output="data/processed",
                size=result.get('size', 256),
                quality=90,
                train_ratio=result.get('train_ratio', 0.7),
                val_ratio=result.get('val_ratio', 0.15),
                test_ratio=result.get('test_ratio', 0.15),
                seed=42,
                keep_temp=False,
                min_size=100
            )
            # Run the generator
            run_dataset_generator(args=args_mock)
            
        elif tool == "web_crawler":
            console.print("[blue]🤖 Preparing web crawler...[/blue]")
            launch_web_crawler(auto_config=result)


def main():
    parser = argparse.ArgumentParser(
        description='AI Tools Suite - Multiple AI applications in one',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                                    # Interactive menu
  python main.py -q "cats" -n 100 --name "Cats"    # Direct dataset generator
        """
    )
    
    parser.add_argument('--query', '-q', type=str, help='Search query for images')
    parser.add_argument('--num', '-n', type=int, help='Number of images to download')
    parser.add_argument('--name', type=str, help='Name for the dataset')
    parser.add_argument('--description', '-d', type=str, default="", help='Description of the dataset')
    parser.add_argument('--output', '-o', type=str, default="data/processed", help='Output base directory')
    parser.add_argument('--size', '-s', type=int, default=256, help='Target image size in pixels')
    parser.add_argument('--quality', type=int, default=90, help='JPEG quality (1-100)')
    parser.add_argument('--train-ratio', type=float, default=0.7, help='Training set ratio')
    parser.add_argument('--val-ratio', type=float, default=0.15, help='Validation set ratio')
    parser.add_argument('--test-ratio', type=float, default=0.15, help='Test set ratio')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--keep-temp', action='store_true', help='Keep temporary files')
    parser.add_argument('--min-size', type=int, default=100, help='Minimum image size')
    
    args = parser.parse_args()
    
    try:
        # If command line args provided, go straight to dataset generator
        if args.query and args.num and args.name:
            success = run_dataset_generator(args)
            sys.exit(0 if success else 1)
        
        # Main menu loop
        while True:
            choice = show_application_menu()
            
            if choice == "1":
                # Dataset Generator
                console.print()
                run_dataset_generator()
                
                # Ask if return to menu
                console.print()
                if not Confirm.ask("[yellow]Return to main menu?[/yellow]", default=True):
                    break
                    
            elif choice == "2":
                # Web Crawler
                console.print()
                launch_web_crawler()
                
                # Ask if return to menu
                console.print()
                if not Confirm.ask("[yellow]Return to main menu?[/yellow]", default=True):
                    break

            elif choice == "3":
                # AI Assistant
                run_ai_assistant()
                
            elif choice == "4":
                # Exit
                console.print()
                goodbye_panel = Panel(
                    "[bold cyan]Thank you for using AI Tools Suite![/bold cyan]\n\n"
                    "[yellow]Come back soon! 👋[/yellow]",
                    title="[bold green]👋 Goodbye![/bold green]",
                    border_style="green",
                    box=box.DOUBLE
                )
                console.print(Align.center(goodbye_panel))
                console.print()
                sys.exit(0)
            
    except KeyboardInterrupt:
        console.print("\n")
        console.rule("[yellow]Operation Cancelled[/yellow]", style="yellow")
        console.print("\n[yellow]⚠️  Application closed by user[/yellow]\n")
        sys.exit(130)
    except Exception as e:
        show_error(str(e))
        import traceback
        console.print("[dim]" + traceback.format_exc() + "[/dim]")
        sys.exit(1)


if __name__ == "__main__":
    main()
