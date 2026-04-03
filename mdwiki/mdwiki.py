import json
import math
import os
import re
import shutil
from pathlib import Path

import markdown
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader


UNKNOWN_READ_COUNT = "未知"


def __all_html_fiels_info(html_dir, page_size):
    """
    鍦╠ist鏍圭洰褰曠殑鐩存帴缃《
    :param html_dir:
    :param page_size:
    :return:
    """
    info = {}  # 0:[(url, title, pub_date, read_cnt)]

    temp_info = []
    top_fix = []  # 缃《鏂囩珷
    html_list = list(Path(html_dir).glob("**/*.html"))

    for html in html_list:
        relative_path = html.relative_to(html_dir)
        relative_url = relative_path.as_posix()
        pub_date = "-".join([str(x) for x in relative_path.parts[:-1]])
        item = (relative_url, relative_path.stem, pub_date, UNKNOWN_READ_COUNT)
        if pub_date == "":
            top_fix.append(item)
        else:
            temp_info.append(item)

    new_info = sorted(temp_info, key=lambda x: x[2], reverse=True)
    post_len = len(new_info)
    page_cnt = math.ceil(post_len / page_size)
    for i in range(0, page_cnt):
        info[i] = new_info[i * page_size : min(i * page_size + page_size, post_len)]

    return info, top_fix


def __all_md_files(md_source_dir, dist_dir):
    md_2_html_path = {}
    md_list = list(Path(md_source_dir).glob("**/*.md"))
    md_list += list(Path(md_source_dir).glob("**/*.MD"))
    for md in md_list:
        html_file_name = f"{md.stem}.html"
        p = str(md.relative_to(md_source_dir).parent)
        p = re.sub(r"[\\/]", "-", p)
        html_path = Path(f"{dist_dir}/{p}/{html_file_name}")
        Path(html_path.parent).mkdir(parents=True, exist_ok=True)
        md_2_html_path[str(md)] = str(html_path)
    return md_2_html_path


def __process_image(mdpath, source_dir, dist_dir, html, html_file):
    soup = BeautifulSoup(html, "lxml")
    images = soup.find_all("img")
    for img in images:
        src = img.get("src")
        if src is not None and not src.startswith("http"):  # 璇存槑鏄湰鍦板浘鐗?
            s = f"{Path(mdpath).parent}/{src}"
            d = f"{dist_dir}/{Path(html_file).relative_to(dist_dir).parent}/{src}"
            Path(Path(d).parent).mkdir(parents=True, exist_ok=True)
            shutil.copy(s, d)


def __copy_cname(source_dir, dist_dir):
    file = f"{source_dir}/CNAME"
    if os.path.exists(file):
        shutil.copy(file, dist_dir)


def __copy_resource(template_theme_dir, theme_static, dist_dir):
    for x in theme_static:
        source_dir = f"{template_theme_dir}/{x}"
        dist = f"{dist_dir}/{x}"
        if not os.path.exists(source_dir):
            Path(dist).mkdir(parents=True, exist_ok=True)
            continue
        shutil.copytree(source_dir, dist, dirs_exist_ok=True)


def __get_config(cfg_file="config.json"):
    """
    濡傛灉褰撳墠鐩綍鏈夊氨鐢紝鍚﹀垯鐢ㄨ嚜甯︾殑榛樿
    :param cfg_file:
    :return:
    """
    bin_dir = str(Path(__file__).parent)
    default_cfg = Path(f"{bin_dir}/config.json")
    override_cfg = Path(cfg_file)

    if not default_cfg.exists():
        print("娌℃壘鍒癱onfig.json, 涓€鑸簲灏嗚浣嶄簬浣犵殑鍗氬鏈€澶栧眰")
        raise SystemExit(-1)

    with open(default_cfg, "r", encoding="utf-8") as f:
        json_obj = json.load(f)

    if override_cfg.exists():
        with open(override_cfg, "r", encoding="utf-8") as f:
            json_obj.update(json.load(f))

    return {
        "template_dir": f"{bin_dir}/{json_obj['template_dir']}",
        "theme": json_obj["theme"],
        "theme_static": json_obj["theme_static"],
        "markdown_extensions": json_obj["markdown_extensions"],
        "page_size": json_obj["page_size"],
        "pagger_len": json_obj["pagger_len"],
        "goatcounter_script": json_obj.get("goatcounter_script", "").strip(),
    }


def __goatcounter_enabled(config):
    return bool(config.get("goatcounter_script"))


def __detail_context(config, html_file, dist_dir, static_path, title, tags, table_of_content, html):
    page_path = "/" + Path(html_file).relative_to(dist_dir).as_posix()
    return {
        "post_content": html,
        "static_path": static_path,
        "title": title,
        "tags": tags,
        "toc": table_of_content,
        "goatcounter_script": config["goatcounter_script"],
        "goatcounter_enabled": __goatcounter_enabled(config),
        "goatcounter_path": page_path,
    }


def __shared_page_context(config, static_path, title=None):
    context = {
        "static_path": static_path,
        "goatcounter_script": config["goatcounter_script"],
        "goatcounter_enabled": __goatcounter_enabled(config),
    }
    if title is not None:
        context["title"] = title
    return context


def main(source_dir, dist_dir):
    config = __get_config("config.json")
    template_dir = config["template_dir"]
    theme = config["theme"]
    theme_static = config["theme_static"]
    markdown_extentions = config["markdown_extensions"]
    page_size = config["page_size"]
    pagger_len = config["pagger_len"]

    template_theme_dir = f"{template_dir}/{theme}"
    env = Environment(loader=FileSystemLoader(template_theme_dir))
    detail_template = env.get_template("detail.html")
    index_template = env.get_template("index.html")

    md_2_html = __all_md_files(source_dir, dist_dir)
    tags_article = {}
    for md, html_file in md_2_html.items():
        Path(Path(html_file).parent).mkdir(parents=True, exist_ok=True)
        with open(md, "r", encoding="utf-8") as f:
            mdobj = markdown.Markdown(extensions=list(markdown_extentions))
            html = mdobj.convert(f.read())
            tags = mdobj.Meta.get("tags")
            table_of_content = mdobj.toc
            mdobj.toc = None
            if tags:
                for t in tags:
                    articles = tags_article.get(t)
                    if articles is None:
                        tags_article[t] = []
                    tags_article[t].append(Path(html_file).relative_to(dist_dir).as_posix())

            __process_image(md, source_dir, dist_dir, html, html_file)
        static_path = "../" * (len(Path(html_file).relative_to(dist_dir).parents) - 1)
        title = Path(html_file).stem
        detail_template.stream(
            **__detail_context(
                config,
                html_file,
                dist_dir,
                static_path,
                title,
                tags,
                table_of_content,
                html,
            )
        ).dump(html_file, encoding="utf-8")

    __copy_resource(template_theme_dir, theme_static, dist_dir)

    pagegger_info, top_fix = __all_html_fiels_info(dist_dir, page_size)
    total_page = len(pagegger_info.keys())
    for idx, post_list in pagegger_info.items():
        if idx == 0:
            list_page = f"{dist_dir}/index.html"
        else:
            list_page = f"{dist_dir}/index_{idx}.html"
        static_path = "../" * (len(Path(list_page).relative_to(dist_dir).parents) - 1)

        start_page = max(0, idx - pagger_len // 2)
        end_page = min(total_page, idx + pagger_len // 2)
        if idx - pagger_len // 2 < 0:
            start_page = 0
            end_page = min(total_page, 0 + pagger_len)
        elif idx + pagger_len // 2 > total_page:
            start_page = max(0, total_page - pagger_len)
            end_page = total_page

        pagger_idx = range(start_page, end_page)
        index_template.stream(
            post=top_fix + post_list,
            pagegger=pagegger_info,
            pagger_idx=pagger_idx,
            cur_page=idx,
            **__shared_page_context(config, static_path),
        ).dump(list_page, encoding="utf-8")
    __copy_cname(source_dir, dist_dir)

    tag_template = env.get_template("tag.html")
    Path(f"{dist_dir}/tags").mkdir(parents=True, exist_ok=True)
    for tag, article_list in tags_article.items():
        new_article_list = [(f"../{x}", Path(x).stem, x[0 : -len(Path(x).name)]) for x in article_list]
        tag_template.stream(
            post=new_article_list,
            **__shared_page_context(config, "../", title=f"鍒嗙被_{tag}"),
        ).dump(f"{dist_dir}/tags/tag_{tag}.html", encoding="utf-8")


if __name__ == "__main__":
    cur_dir = Path(__file__).parent
    print(cur_dir)
