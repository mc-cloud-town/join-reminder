from __future__ import annotations
from datetime import datetime, timedelta
import json
from pathlib import Path
import re

from mcdreforged.api.all import (
    Info,
    PluginServerInterface,
    RTextList,
    RText,
    RColor,
    RAction,
)

config_path = Path("config/reminder.json")
FORMAT_CODE = re.compile(r"(?<!\$)\$[0-9a-gklmnor]")

PREFIX = "!!motd"
HELP_MESSAGE = (
    "================== §bjoin reminder§r ==================\n"
    f"§b{PREFIX} §r 顯示所有提醒\n"
    f"§b{PREFIX} help §r 顯示幫助\n"
    f"§b{PREFIX} del <name> §r 添加提醒\n"
    f"§b{PREFIX} <name> [duration] §r 添加 <name> 提醒\n"
    " ".zfill(len(PREFIX)) + " <duration> 為提醒截止間隔 (1d2h3m4s)\n"
)


list_dic: dict[str, str] = {}


def read():
    global list_dic
    try:
        list_dic = json.load(config_path.read_text(encoding="utf-8"))
    except Exception:
        save()


def save():
    config_path.write_text(
        json.dumps(list_dic, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )


def search(name: str) -> tuple[str, str] | None:
    for k, v in list_dic.items():
        if name == k:
            return k, v

    return None


def parse_format(text: str) -> str:
    return FORMAT_CODE.sub(
        lambda x: x.group(0).replace("$", "§"),
        text,
    ).replace("$$", "$")


def parse_interval(str_interval: str) -> int:
    if str_interval.startswith("-"):
        return -1
    digit, result = "", 0
    time_map = {"s": 1, "m": 60, "h": 3600, "d": 3600 * 24}

    def add(s: str = "") -> tuple[int, int]:
        return result + int(digit or 1) * time_map.get(s, 1), ""

    for s in str_interval + " ":
        if s.isdigit():
            digit += s
        elif s in time_map:
            result, digit = add(s)

    if digit:
        result, _ = add()

    return int(datetime.now() + timedelta(seconds=result))


def list_info() -> RTextList:
    lists: list[RTextList] = []
    for name, time in list_dic.items():
        if time == -1:
            time_str = "永久"
        elif (time_ := datetime.fromtimestamp(time)) < datetime.now():
            del list_dic[name]
            continue
        else:
            time_str = time_.strftime("%Y-%m-%d %H:%M:%S")

        lists.append(
            RTextList(
                "- ",
                RText("[x]", color=RColor.red)
                .c(
                    RAction.suggest_command,
                    f"{PREFIX} del {name}",
                )
                .h(RText("刪除", color=RColor.red)),
                RText(f" {name}", color=RColor.aqua)
                .c(f"{PREFIX} add {name} {time}")
                .h(
                    "點擊以修改訊息\n",
                    RText("截止時間: ", color=RColor.gray),
                    RText(time_str, color=RColor.gold),
                ),
            )
        )
    return RTextList(*lists)


def on_info(server: PluginServerInterface, info: Info):
    if (
        info.is_user
        and info.is_from_server
        and info.content
        and info.content.startswith(PREFIX)
    ):
        args = info.content.split(" ")
        # {PREFIX}
        if (len_args := len(args)) == 1:
            server.tell(info, list_info())
            return

        arg1 = args[1]
        if len_args == 2:
            # {PREFIX} help
            if arg1 == "help":
                server.tell(info.player, HELP_MESSAGE)
                return
            # {PREFIX} <name>
            list_dic[parse_format(arg1)] = -1
        elif len_args == 3:
            # {PREFIX} del <name>
            if arg1 == "del" or arg1 == "d":
                if (arg := args[2]) in list_dic:
                    del list_dic[arg]
                    server.tell(info.player, f"§b{arg}§r 已刪除")
                else:
                    server.tell(info.player, f"§b{arg}§r 不存在")
            # {PREFIX} <name> <duration>
            else:
                list_dic[parse_format(arg1)] = parse_interval(args[2])
        else:
            server.tell(info.player, HELP_MESSAGE)
            return
        save()


def on_player_joined(server: PluginServerInterface, player_name: str, info: Info):
    server.tell(player_name, list_info())
