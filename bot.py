import discord, json, time, datetime, os, sys, subprocess
from discord.ext import commands
from source.functions.colors import colors as cr

from dotenv import load_dotenv
load_dotenv()

class Client(commands.AutoShardedBot):
    def __init__(self, intents: discord.Intents, **kwargs):
        super().__init__(command_prefix=".", intents=intents, shard_count=1, **kwargs)
        self.start_time = datetime.datetime.now()
        self.added = False
        self.date = (cr.GREY + time.strftime("%Y-%m-%d %H:%M:%S") + cr.ENDC)
    async def setup_hook(self):
        with open("config/load.json", "r") as f:
            data = json.load(f)

        for extension in data.get("commands", []) + data.get("modules", []):
            load_path = extension.get("load_path")
            if not load_path:
                print(self.date + cr.WARNING + " WARN" + cr.CYAN + f"     Skipping extension {extension.get('name')} because 'load_path' is not specified." + cr.ENDC)
                continue

            try:
                await self.load_extension(load_path)
                print(self.date + cr.BLUE + " INFO" + cr.CYAN + f"     Loaded {extension['name']}" + cr.ENDC)
            except Exception as exc:
                print(self.date + cr.FAIL + " ERROR" + cr.CYAN + f"    Could not load {load_path} due to {exc.__class__.__name__}: {exc}" + cr.ENDC)

    async def on_ready(self):
        sync = await self.tree.sync()
        print(self.date + cr.BLUE +  " INFO" + cr.CYAN + f"     {self.user.name}#{self.user.discriminator} just woke up!" + cr.ENDC)
        print(self.date + cr.BLUE +  " INFO" + cr.CYAN + f"     Synced {len(sync)} commands" + cr.ENDC)

        if not self.added:
            self.added = True
        

intents = discord.Intents.all()
client = Client(intents=intents)
client.remove_command("help")
owner_id = 614807913302851594 # Replace with your ID

with open('config/load.json', 'r') as file:
    load_data = json.load(file)

@client.command()
async def dev(ctx, *args):
    if ctx.author.id != owner_id:
        return

    if not args:
        await ctx.send("Invalid usage. Please provide at least one argument.")
        return

    action = args[0]
    handlers = {
        'load': load_extension,
        'unload': unload_extension,
        'reload': reload_extension,
        'load_f': load_function,
        'reload_f': reload_function,
        'reload_all': reload_all_extensions,
        'shutdown': shutdown_bot,
        'sd': shutdown_bot,
        'restart': restart_bot,
        'rs': restart_bot,
        'sync': sync
    }

    handler = handlers.get(action)
    if handler:
        await handler(ctx, args[1:])
    else:
        supported_actions = ', '.join(handlers.keys())
        await ctx.send(f"Invalid action. Supported actions: `{supported_actions}`.")
        
async def restart_bot(ctx, args):
    await client.close()
    subprocess.Popen([sys.executable, "bot.py"])
    sys.exit(0)
    
async def load_extension(ctx, args):
    if len(args) < 3:
        await ctx.send("Invalid usage. Please provide category, command, and full path to load.")
        return

    category, command_name, full_path = args
    if full_path.startswith('source.commands'):
        try:
            await client.load_extension(full_path)
            await ctx.send(f"Loaded command: {command_name} from full path: {full_path}")
            print(f"Loaded command: {command_name} from full path: {full_path}")
        except Exception as e:
            
            await ctx.send(f"Failed to load command: {command_name}\n{type(e).__name__}: {e}")
            print(f"Failed to load command: {command_name} {type(e).__name__}: {e}")
    else:
        await ctx.send("Invalid command path.")

async def unload_extension(ctx, args):
    if len(args) < 2:
        await ctx.send("Invalid usage. Please provide category and command to unload.")
        return

    category, command_name = args
    command = next((cmd for cmd in load_data['commands'] if cmd['category'] == category and cmd['name'] == command_name), None)
    if command:
        try:
            await client.unload_extension(command['load_path'])
            await ctx.send(f"Unloaded command: {command['name']} from category: {category}")
            print(f"Unloaded command: {command['name']} from category: {category}")
        except Exception as e:
            
            await ctx.send(f"Failed to unload command: {command['name']} from category: {category}\n{type(e).__name__}: {e}")
            print(f"Failed to unload command: {command['name']} from category: {category} {type(e).__name__}: {e}")
    else:
        await ctx.send("Command not found.")

async def reload_extension(ctx, args):
    if len(args) < 2:
        await ctx.send("Invalid usage. Please provide category and command to reload.")
        return

    category, command_name = args
    command = next((cmd for cmd in load_data['commands'] if cmd['category'] == category and cmd['name'] == command_name), None)
    if command:
        try:
            await client.reload_extension(command['load_path'])
            await ctx.send(f"Reloaded command: {command['name']} from category: {category}")
            print(f"Reloaded command: {command['name']} from category: {category}")
        except Exception as e:
            
            await ctx.send(f"Failed to reload command: {command['name']}\n{type(e).__name__}: {e}")
            print(f"Failed to reload command: {command['name']} {type(e).__name__}: {e}")
    else:
        await ctx.send("Command not found.")

async def load_function(ctx, args):
    if len(args) < 2:
        await ctx.send("Invalid usage. Please provide function name and full path to load.")
        return

    function_name, full_path = args
    if full_path.startswith('source.modules'):
        try:
            await client.load_extension(full_path)
            await ctx.send(f"Loaded function: {function_name} from full path: {full_path}")
            print(f"Loaded function: {function_name} from full path: {full_path}")
        except Exception as e:
            
            await ctx.send(f"Failed to load function: {function_name} from full path: {full_path}\n{type(e).__name__}: {e}")
            print(f"Failed to load function: {function_name} from full path: {full_path} {type(e).__name__}: {e}")
    else:
        await ctx.send("Invalid function path.")

async def reload_function(ctx, args):
    if len(args) < 1:
        await ctx.send("Invalid usage. Please provide function name to reload.")
        return

    function_name = args[0]
    function_data = next((func for func in load_data['modules'] if func['name'] == function_name), None)
    if function_data:
        try:
            await client.reload_extension(function_data['load_path'])
            await ctx.send(f"Reloaded function: {function_data['name']} from full path: {function_data['load_path']}")
            print(f"Reloaded function: {function_data['name']} from full path: {function_data['load_path']}")
        except Exception as e:
            
            await ctx.send(f"Failed to reload function: {function_data['name']}\n{type(e).__name__}: {e}")
            print(f"Failed to reload function: {function_data['name']} {type(e).__name__}: {e}")
    else:
        await ctx.send("Function not found.")
        print(f"Function not found: {function_name}")

async def reload_all_extensions(ctx, _):
    message = await ctx.send("Reloading all extensions...")
    reloaded_count = 0

    for extension in load_data.get('commands', []) + load_data.get('modules', []):
        load_path = extension.get('load_path')
        if not load_path:
            continue  # Skip if there is no load_path
        
        try:
            await client.reload_extension(load_path)
            reloaded_count += 1
        except Exception as e:
            await ctx.send(f"Failed to reload {load_path}\n{type(e).__name__}: {e}")

    await message.edit(content=f"Reloaded {reloaded_count} extensions.")

async def shutdown_bot(ctx, _):
    sys.exit(0)

async def sync(ctx, _):
    if ctx.author.id != 614807913302851594:
        return 
    await ctx.send("Syncing...")
    await client.tree.sync()
    await ctx.send("Synced all commands!")
    
client.run(os.getenv("TOKEN"))