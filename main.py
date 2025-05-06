import os
import json
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import astrbot.api.message_components as Comp

@register("备忘录", "Koikokokokoro", "简易备忘录", "0.1.0")
class MemoPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        base = os.getcwd()
        self.plugin_dir = os.path.join(base, "data", "plugins", "astrbot_plugin_memo")
        os.makedirs(self.plugin_dir, exist_ok=True)
        self.memo_file = os.path.join(self.plugin_dir, "memos.json")
        if not os.path.exists(self.memo_file):
            with open(self.memo_file, 'w', encoding='utf-8') as f:
                json.dump({}, f)

    def _load(self):
        try:
            with open(self.memo_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"读取备忘录失败: {e}")
            return {}

    def _save(self, data):
        try:
            with open(self.memo_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存备忘录失败: {e}")

    @filter.command("备忘")
    async def add_memo(self, event: AstrMessageEvent, content: str):
        """用法：/备忘 <对象> <内容>"""
        parts = content.strip().split(maxsplit=1)
        if len(parts) < 2:
            yield event.plain_result("格式错误，用法：/备忘 <对象> <内容>")
            return
        target, note = parts
        uid = str(event.get_sender_id())
        data = self._load()
        user_list = data.get(uid, [])
        user_list.append({"target": target, "content": note})
        data[uid] = user_list
        self._save(data)
        yield event.plain_result(f"已添加备忘：[{target}] {note}")

    @filter.command("查询")
    async def list_memo(self, event: AstrMessageEvent):
        """显示所有备忘"""
        uid = str(event.get_sender_id())
        data = self._load()
        user_list = data.get(uid, [])
        if not user_list:
            yield event.plain_result("暂无备忘记录。")
            return
        lines = [f"{idx}. [{itm['target']}] {itm['content']}" for idx, itm in enumerate(user_list,1)]
        yield event.plain_result("备忘列表：\n" + "\n".join(lines))

    @filter.command("删除")
    async def del_memo(self, event: AstrMessageEvent, target: str):
        """用法：/删除 <对象>"""
        uid = str(event.get_sender_id())
        data = self._load()
        user_list = data.get(uid, [])
        new_list = [itm for itm in user_list if itm['target'] != target]
        removed = len(user_list) - len(new_list)
        if removed == 0:
            yield event.plain_result(f"未找到与 [{target}] 相关的备忘。")
            return
        data[uid] = new_list
        self._save(data)
        yield event.plain_result(f"已删除 {removed} 条与 [{target}] 相关的备忘。")

    async def terminate(self):
        logger.info("备忘录插件已停用")
