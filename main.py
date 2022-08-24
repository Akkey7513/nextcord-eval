import io
import ast
import nextcord
import traceback
import contextlib
from nextcord.ext import commands

config = {
    "owner": 0, # ID of the user who is allowed to execute the command.
    "token": "" # Token of the bot that executes this code.
}

intents = nextcord.Intents(messages=True, message_content=True)
bot = commands.Bot(command_prefix="!", help_command=None, owner_id=config["owner"], intents=intents)

def insert_returns(body):
    if isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(body[-1].value)
        ast.fix_missing_locations(body[-1])
    if isinstance(body[-1], ast.If):
        insert_returns(body[-1].body)
        insert_returns(body[-1].orelse)
    if isinstance(body[-1], ast.With):
        insert_returns(body[-1].body)

@bot.event
async def on_ready():
    print("Logged In")

@bot.command()
@commands.is_owner()
async def runeval(runeval):
    await runeval.reply("Please send the code to be executed.")
    def check_author(m):
        return runeval.author.id == m.author.id
    msg = await bot.wait_for("message", check=check_author)
    func_name = f"_eval{str(runeval.author.id)}"
    cmd = msg.content.replace("```py", "").replace("```python", "")
    cmd = "\n".join(f"    {i}" for i in cmd.splitlines())
    func_cmd = f"async def {func_name}():\n{cmd}"
    parsed_func = ast.parse(func_cmd)
    func_cmd = parsed_func.body[0].body
    insert_returns(func_cmd)
    exec(compile(parsed_func, filename="<runeval>", mode="exec"))
    return_value = "null"
    output_value = io.StringIO(initial_value="null")
    try:
        with contextlib.redirect_stdout(output_value):
            return_value = (await eval(f"{func_name}()"))
    except:
        return_value = traceback.format_exc()
    result_embed = nextcord.Embed(title="Result", description="The result of executing the code is displayed. The return value from the function and the output to the console are displayed.")
    result_embed.add_field(name="Return", value=f"```\n{return_value}\n```", inline=False)
    result_embed.add_field(name="Output", value=f"```\n{output_value.getvalue()}\n```", inline=False)
    await runeval.reply(embed=result_embed)

bot.run(config["token"])