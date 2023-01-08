import asyncio
import re
from io import BytesIO
from os import remove

import aiofiles
from gpytranslate import Translator
from pyrogram import enums, filters
from pyrogram.errors import MessageTooLong, PeerIdInvalid
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from wikipedia import summary
from wikipedia.exceptions import DisambiguationError, PageError

from Powers import *
from Powers.bot_class import Gojo
from Powers.database.users_db import Users
from Powers.utils.clean_file import remove_markdown_and_html
from Powers.utils.custom_filters import command
from Powers.utils.http_helper import *
from Powers.utils.extract_user import extract_user
from Powers.utils.parser import mention_html


@Gojo.on_message(command("wiki"))
async def wiki(_, m: Message):

    if len(m.text.split()) <= 1:
        return await m.reply_text(
            text="Please check help on how to use this this command."
        )

    search = m.text.split(None, 1)[1]
    try:
        res = summary(search)
    except DisambiguationError as de:
        return await m.reply_text(
            f"Disambiguated pages found! Adjust your query accordingly.\n<i>{de}</i>",
            parse_mode=enums.ParseMode.HTML,
        )
    except PageError as pe:
        return await m.reply_text(f"<code>{pe}</code>", parse_mode=enums.ParseMode.HTML)
    if res:
        result = f"<b>{search}</b>\n\n"
        result += f"<i>{res}</i>\n"
        result += f"""<a href="https://id.wikipedia.org/wiki/{search.replace(" ", "%20")}">Read more...</a>"""
        try:
            return await m.reply_text(
                result,
                parse_mode=enums.ParseMode.HTML,
                disable_web_page_preview=True,
            )
        except MessageTooLong:
            with BytesIO(str.encode(await remove_markdown_and_html(result))) as f:
                f.name = "result.txt"
                return await m.reply_document(
                    document=f,
                    quote=True,
                    parse_mode=enums.ParseMode.HTML,
                )
    await m.stop_propagation()


@Gojo.on_message(command("gdpr"))
async def gdpr_remove(_, m: Message):
    if m.from_user.id in SUPPORT_STAFF:
        await m.reply_text(
            "You're in my support staff, I cannot do that unless you are no longer a part of it!",
        )
        return

    Users(m.from_user.id).delete_user()
    await m.reply_text(
        "Your personal data has been deleted.\n"
        "Note that this will not unban you from any chats, as that is telegram data, not Gojo data."
        " Flooding, warns, and gbans are also preserved, as of "
        "[this](https://ico.org.uk/for-organisations/guide-to-the-general-data-protection-regulation-gdpr/individual-rights/right-to-erasure/),"
        " which clearly states that the right to erasure does not apply 'for the performance of a task carried out in the public interest', "
        "as is the case for the aforementioned pieces of data.",
        disable_web_page_preview=True,
    )
    await m.stop_propagation()


'''
@Gojo.on_message(
    command("lyrics") & (filters.group | filters.private),
)
async def get_lyrics(_, m: Message):
    if len(m.text.split()) <= 1:
        await m.reply_text(text="Please check help on how to use this this command.")
        return

    query = m.text.split(None, 1)[1]
    song = ""
    if not query:
        await m.edit_text(text="You haven't specified which song to look for!")
        return
    song_name = query
    em = await m.reply_text(text=f"Finding lyrics for <code>{song_name}<code>...")
    song = Song.find_song(query)
    if song:
        if song.lyrics:
            reply = song.format()
        else:
            reply = "Couldn't find any lyrics for that song!"
    else:
        reply = "Song not found!"
    try:
        await em.edit_text(reply)
    except MessageTooLong:
        with BytesIO(str.encode(await remove_markdown_and_html(reply))) as f:
            f.name = "lyrics.txt"
            await m.reply_document(
                document=f,
            )
        await em.delete()
    return
'''


@Gojo.on_message(
    command("id") & (filters.group | filters.private),
)
async def id_info(c: Gojo, m: Message):

    ChatType = enums.ChatType
    if m.chat.type == ChatType.SUPERGROUP and not m.reply_to_message:
        await m.reply_text(text=f"This Group's ID is <code>{m.chat.id}</code>")
        return

    if m.chat.type == ChatType.PRIVATE and not m.reply_to_message:
        await m.reply_text(text=f"Your ID is <code>{m.chat.id}</code>.")
        return

    user_id, _, _ = await extract_user(c, m)
    if user_id:
        if m.reply_to_message and m.reply_to_message.forward_from:
            user1 = m.reply_to_message.from_user
            user2 = m.reply_to_message.forward_from
            orig_sender = ((await mention_html(user2.first_name, user2.id)),)
            orig_id = (f"<code>{user2.id}</code>",)
            fwd_sender = ((await mention_html(user1.first_name, user1.id)),)
            fwd_id = (f"<code>{user1.id}</code>",)
            await m.reply_text(
                text=f"""Original Sender - {orig_sender} (<code>{orig_id}</code>)
        Forwarder - {fwd_sender} (<code>{fwd_id}</code>)""",
                parse_mode=enums.ParseMode.HTML,
            )
        else:
            try:
                user = await c.get_users(user_id)
            except PeerIdInvalid:
                await m.reply_text(
                    text="""Failed to get user
      Peer ID invalid, I haven't seen this user anywhere earlier, maybe username would help to know them!"""
                )
                return

            await m.reply_text(
                f"{(await mention_html(user.first_name, user.id))}'s ID is <code>{user.id}</code>.",
                parse_mode=enums.ParseMode.HTML,
            )
    elif m.chat.type == ChatType.PRIVATE:
        await m.reply_text(text=f"Your ID is <code>{m.chat.id}</code>.")
    else:
        await m.reply_text(text=f"This Group's ID is <code>{m.chat.id}</code>")
    return


@Gojo.on_message(
    command("gifid") & (filters.group | filters.private),
)
async def get_gifid(_, m: Message):
    if m.reply_to_message and m.reply_to_message.animation:
        LOGGER.info(f"{m.from_user.id} used gifid cmd in {m.chat.id}")
        await m.reply_text(
            f"Gif ID:\n<code>{m.reply_to_message.animation.file_id}</code>",
            parse_mode=enums.ParseMode.HTML,
        )
    else:
        await m.reply_text(text="Please reply to a gif to get it's ID.")
    return


@Gojo.on_message(
   command(["ship"]) & (filters.group | filters.private),
)
async def shiping(_, m: Message):
    if len(m.text.split()) == 2:
        username = m.text.split(maxsplit=1)[1]
        LOGGER.info(f"{m.from_user.id} used shiping cmd in {m.chat.id}")
    else:
        await m.reply_text(
            f"😅 Maaf, perintah ini hanya untuk owner.",
        )
        return
    username = username.split("/")[-1]
    URL = f"https://tebakgambar.akurak.repl.co/love/{username}.json"
    try:
        r = await get(URL, timeout=5)
    except asyncio.TimeoutError:
        return await m.reply_text("request timeout")
    except Exception as e:
        return await m.reply_text(f"ERROR: `{e}`")

    avtar = r.get("lovegif", None)
    usersa = r.get("usersatu", None)
    idsa = r.get("idsatu", None)
    
    userdu = r.get("userdua", None)
    iddu = r.get("iddua", None)
    

    REPLY = ""
    if idsa:
        REPLY += f"Pasangan hari ini:\n<a href='tg://openmessage?user_id={idsa}'>{usersa}</a>"
    REPLY += f" + <a href='tg://openmessage?user_id={iddu}'>{userdu}</a> = ❤️\n\nPasangan baru hari ini dapat dipilih pada pukul 05.00 WIB"
        

    if avtar:
        return await m.reply_animation(animation=f"{avtar}", caption=REPLY)
    await m.reply_text(REPLY)
    return


@Gojo.on_message(
   command(["imdb"]) & (filters.group | filters.private),
)
async def imdb(_, m: Message):
    if len(m.text.split()) == 2:
        username = m.text.split(maxsplit=1)[1]
        LOGGER.info(f"{m.from_user.id} used imdb cmd in {m.chat.id}")
    else:
        await m.reply_text(
            f"Usage: <code>{Config.PREFIX_HANDLER}id imdb</code>",
        )
        return
    username = username.split("/")[-1]
    URL = f"https://www.omdbapi.com/?apikey=95cc8ace&i={username}"
    try:
        r = await get(URL, timeout=5)
    except asyncio.TimeoutError:
        return await m.reply_text("request timeout")
    except Exception as e:
        return await m.reply_text(f"ERROR: `{e}`")

    avtar = r.get("Poster", None)
    rntime = r.get("Runtime", None)
    name = r.get("Title", None)
    company = r.get("company", None)
    rlis = r.get("Released", 0)
    gnre = r.get("Genre", 0)
    public_repos = r.get("imdbRating", 0)
    bio = r.get("Plot", None)
    negara = r.get("Country", "Not Found")
    location = r.get("location", None)
    email = r.get("email", None)
    bhsa = r.get("Language", "Not Found")
    blog = r.get("blog", None)
    twitter = r.get("twitter_username", None)
    strdara = r.get("Director", 0)
    pnlis = r.get("Writer", None)
    artis = r.get("Actors", "Not Found")
    tipe = r.get("Type", "Not Found")
    voter = r.get("imdbVotes", "Not Found")


    REPLY = ""
    if name:
        REPLY += f"<b>📹 Judul:</b> {name} ({tipe})"
    if rntime:
        REPLY += f"\n<b>Durasi:</b> {rntime}"
    REPLY += f"\n<b>Rating:</b> {public_repos} dari {voter} pengguna"
    REPLY += f"\n<b>Rilis:</b> {rlis}"
    REPLY += f"\n<b>Genre:</b> {gnre}"
    if email:
        REPLY += f"\n<b>✉️ Email:</b> <code>{email}</code>"
    if company:
        org_url = company.strip("@")
        REPLY += f"\n<b>™️ Organization:</b> <a href='https://github.com/{org_url}'>{company}</a>"
    if blog:
        bname = blog.split(".")[-2]
        bname = bname.split("/")[-1]
        REPLY += f"\n<b>📝 Blog:</b> <a href={blog}>{bname}</a>"
    if twitter:
        REPLY += f"\n<b>⚜️ Twitter:</b> <a href='https://twitter.com/{twitter}'>{twitter}</a>"
    if location:
        REPLY += f"\n<b>🚀 Location:</b> <code>{location}</code>"
    REPLY += f"\n<b>Negara:</b> <code>{negara}</code>"
    REPLY += f"\n<b>Bahasa:</b> <code>{bhsa}</code>"
    REPLY += f"\n\n<b>🙎 Info Cast:\nSutradara:</b> <code>{strdara}</code>"
    pnlisku = pnlis.split(",")[1]
    REPLY += f"\n<b>Penulis:</b> <code>{pnlisku}</code>"
    REPLY += f"\n<b>Pemeran:</b> <code>{artis}</code>"
    if bio:
        REPLY += f"\n\n<b>📜 Plot:</b> <code>{bio}</code>"

    if avtar:
        return await m.reply_photo(photo=f"{avtar}", caption=REPLY)
    await m.reply_text(REPLY)
    return




pattern = re.compile(r"^text/|json$|yaml$|xml$|toml$|x-sh$|x-shellscript$")
BASE = "https://batbin.me/"


async def paste(content: str):
    resp = await post(f"{BASE}api/v2/paste", data=content)
    if not resp["success"]:
        return
    return BASE + resp["message"]


@Gojo.on_message(command("paste"))
async def paste_func(_, message: Message):
    r = message.reply_to_message
    m = await message.reply_text("Pasting...")

    if not r:
        content = message.text.split(None, 1)[1]

    if r:
        if not r.text and not r.document:
            return await m.edit("Only text and documents are supported")

        if r.text:
            content = str(r.text)
        if r.document:
            if r.document.file_size > 40000:
                return await m.edit("You can only paste files smaller than 40KB.")

            if not pattern.search(r.document.mime_type):
                return await m.edit("Only text files can be pasted.")

            doc = await message.reply_to_message.download()

            async with aiofiles.open(doc, mode="r") as f:
                content = await f.read()

            remove(doc)

    link = await paste(content)
    kb = [[InlineKeyboardButton(text="Paste Link ", url=link)]]
    await m.delete()
    try:
        await message.reply_text("Here's your paste", reply_markup=InlineKeyboardMarkup(kb))
    except Exception as e:
        if link:
            return await message.reply_text(f"Here's your paste:\n [link]({link})",)
        return await message.reply_text(f"Failed to post. Due to following error:\n{e}")


@Gojo.on_message(command("tr"))
async def tr(_, message):
    trl = Translator()
    if message.reply_to_message and (
        message.reply_to_message.text or message.reply_to_message.caption
    ):
        if len(message.text.split()) == 1:
            target_lang = "en"
        else:
            target_lang = message.text.split()[1]
        if message.reply_to_message.text:
            text = message.reply_to_message.text
        else:
            text = message.reply_to_message.caption
    else:
        if len(message.text.split()) <= 2:
            await message.reply_text(
                "Provide lang code.\n[Available options](https://telegra.ph/Lang-Codes-02-22).\n<b>Usage:</b> <code>/tr en</code>",
            )
            return
        target_lang = message.text.split(None, 2)[1]
        text = message.text.split(None, 2)[2]
    detectlang = await trl.detect(text)
    try:
        tekstr = await trl(text, targetlang=target_lang)
    except ValueError as err:
        await message.reply_text(f"Error: <code>{str(err)}</code>")
        return
    return await message.reply_text(
        f"<b>Translated:</b> from {detectlang} to {target_lang} \n<code>``{tekstr.text}``</code>",
    )


__PLUGIN__ = "utils"
_DISABLE_CMDS_ = ["ask", "ship", "paste", "imdb", "wiki", "id", "gifid", "tr", "github", "git"]
__alt_name__ = ["util", "misc", "tools"]

__HELP__ = """
**Utils**

Beberapa alat disediakan oleh bot untuk membuat tugas Anda lebih mudah!

• /id: Dapatkan id grup saat ini. Jika digunakan dengan membalas pesan, dapatkan id pengguna tersebut.
• /info: Dapatkan informasi tentang pengguna.
• /imdb '<imd id>': Cari detail drama/film menggunakan imdb api!
• /gifid: Balas gif kepada saya untuk memberi tahu Anda ID file-nya.
• /wiki: '<query>': wiki kueri Anda.
• /tr '<language>': Terjemahkan teks dan kemudian balas kepada Anda dengan bahasa yang telah Anda tentukan, berfungsi sebagai balasan pesan.
• /git '<username>': Cari pengguna menggunakan github api!
• /weebify '' <text>atau '<balas pesan>': Untuk membuat teks.

**Example:**
`/imdb tt1630029`: Ini mengambil informasi tentang film dari database."""
