import json
import math
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import markdown
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader


UNKNOWN_READ_COUNT = "未知"
MANIFEST_FILE = ".mdwiki-build.json"


def __relative_html_path(md_path, source_dir, dist_dir):
    html_file_name = f"{md_path.stem}.html"
    parent = str(md_path.relative_to(source_dir).parent)
    parent = re.sub(r"[\\/]", "-", parent)
    html_path = Path(f"{dist_dir}/{parent}/{html_file_name}")
    Path(html_path.parent).mkdir(parents=True, exist_ok=True)
    return html_path


def __all_md_files(md_source_dir, dist_dir):
    md_2_html_path = {}
    md_list = list(Path(md_source_dir).glob("**/*.md"))
    md_list += list(Path(md_source_dir).glob("**/*.MD"))
    for md in md_list:
        md_2_html_path[str(md)] = str(__relative_html_path(md, md_source_dir, dist_dir))
    return md_2_html_path


def __process_image(mdpath, source_dir, dist_dir, html, html_file):
    soup = BeautifulSoup(html, "lxml")
    images = soup.find_all("img")
    for img in images:
        src = img.get("src")
        if src is not None and not src.startswith("http"):
            source_image = f"{Path(mdpath).parent}/{src}"
            target_image = f"{dist_dir}/{Path(html_file).relative_to(dist_dir).parent}/{src}"
            source_image_path = Path(source_image)
            if not source_image_path.exists():
                continue
            Path(Path(target_image).parent).mkdir(parents=True, exist_ok=True)
            shutil.copy(source_image, target_image)


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


def __reset_dist_dir(dist_dir):
    dist_path = Path(dist_dir)
    dist_path.mkdir(parents=True, exist_ok=True)
    for child in dist_path.iterdir():
        if child.is_dir():
            shutil.rmtree(child, ignore_errors=True)
        else:
            child.unlink(missing_ok=True)


def __get_config(cfg_file="config.json"):
    """
    如果当前目录有配置，就优先使用；否则使用包内默认配置。
    """
    bin_dir = str(Path(__file__).parent)
    default_cfg = Path(f"{bin_dir}/config.json")
    override_cfg = Path(cfg_file)

    if not default_cfg.exists():
        print("没有找到默认 config.json")
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
        "source_markdown_base_url": json_obj.get("source_markdown_base_url", "").rstrip("/"),
    }


def __goatcounter_enabled(config):
    return bool(config.get("goatcounter_script"))


def __source_markdown_url(config, md_file, source_dir):
    base_url = config.get("source_markdown_base_url", "")
    if not base_url:
        return ""
    relative_md_path = Path(md_file).relative_to(source_dir).as_posix()
    return f"{base_url}/{quote(relative_md_path, safe='/')}"


def __detail_context(config, md_file, source_dir, html_file, dist_dir, static_path, title, tags, table_of_content, html):
    page_path = "/" + Path(html_file).relative_to(dist_dir).as_posix()
    source_markdown_url = __source_markdown_url(config, md_file, source_dir)
    return {
        "post_content": html,
        "static_path": static_path,
        "title": title,
        "tags": tags,
        "toc": table_of_content,
        "build_version": datetime.now().strftime("%Y%m%d"),
        "goatcounter_script": config["goatcounter_script"],
        "goatcounter_enabled": __goatcounter_enabled(config),
        "goatcounter_path": page_path,
        "source_markdown_url": source_markdown_url,
        "source_markdown_enabled": bool(source_markdown_url),
    }


def __shared_page_context(config, static_path, title=None):
    context = {
        "static_path": static_path,
        "goatcounter_script": config["goatcounter_script"],
        "goatcounter_enabled": __goatcounter_enabled(config),
        "build_version": datetime.now().strftime("%Y%m%d"),
    }
    if title is not None:
        context["title"] = title
    return context


def __load_manifest(dist_dir):
    manifest_path = Path(dist_dir) / MANIFEST_FILE
    if not manifest_path.exists():
        return {"posts": {}}
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def __save_manifest(dist_dir, records):
    manifest_path = Path(dist_dir) / MANIFEST_FILE
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now().isoformat(),
        "posts": records,
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)


def __read_changed_files(changed_files):
    if not changed_files:
        return []
    with open(changed_files, "r", encoding="utf-8") as f:
        return [line.strip().replace("\\", "/") for line in f if line.strip()]


def __output_dir_name_for_source_relative(parent_relative):
    parent = str(parent_relative)
    parent = re.sub(r"[\\/]", "-", parent)
    return parent


def __collect_candidate_posts_for_assets(source_dir, asset_paths):
    candidates = set()
    source_dir = Path(source_dir)
    for asset_path in asset_paths:
        asset_path = Path(asset_path)
        source_parent = source_dir / asset_path.parent
        if not source_parent.exists():
            continue
        for md_file in source_parent.glob("*.md"):
            candidates.add(md_file.relative_to(source_dir).as_posix())
        for md_file in source_parent.glob("*.MD"):
            candidates.add(md_file.relative_to(source_dir).as_posix())
    return candidates


def __classify_changed_files(changed_files, source_dir):
    source_root = Path(source_dir).name
    current_posts = {
        path.relative_to(source_dir).as_posix()
        for path in Path(source_dir).glob("**/*.md")
    }
    current_posts.update(
        path.relative_to(source_dir).as_posix()
        for path in Path(source_dir).glob("**/*.MD")
    )

    changed_posts = set()
    changed_assets = set()

    for changed in changed_files:
        changed_path = Path(changed)
        if changed in {"config.json", "CNAME"}:
            return {"mode": "full", "reason": f"{changed} changed"}
        if not changed.startswith(f"{source_root}/"):
            return {"mode": "full", "reason": f"{changed} is outside source tree"}

        relative_to_source = changed_path.relative_to(source_root).as_posix()
        suffix = changed_path.suffix.lower()
        if suffix == ".md":
            changed_posts.add(relative_to_source)
        else:
            changed_assets.add(relative_to_source)

    changed_posts.update(__collect_candidate_posts_for_assets(source_dir, changed_assets))
    changed_posts.update(path for path in changed_posts if path in current_posts)

    return {
        "mode": "incremental",
        "changed_posts": changed_posts,
        "changed_assets": changed_assets,
    }


def __parse_tags(mdobj):
    tags = mdobj.Meta.get("tags")
    if not tags:
        return []
    return [tag.strip() for tag in tags if tag.strip()]


def __build_article_record(md_file, source_dir, dist_dir, markdown_extensions):
    md_path = Path(md_file)
    html_path = __relative_html_path(md_path, source_dir, dist_dir)

    with open(md_path, "r", encoding="utf-8") as f:
        mdobj = markdown.Markdown(extensions=list(markdown_extensions))
        html = mdobj.convert(f.read())
        tags = __parse_tags(mdobj)
        toc = mdobj.toc
        mdobj.toc = None

    return {
        "md_rel": md_path.relative_to(source_dir).as_posix(),
        "html_rel": html_path.relative_to(dist_dir).as_posix(),
        "title": html_path.stem,
        "pub_date": "-".join(html_path.relative_to(dist_dir).parts[:-1]),
        "tags": tags,
        "html": html,
        "toc": toc,
    }


def __render_article(detail_template, config, source_dir, dist_dir, article_record):
    html_file = Path(dist_dir) / article_record["html_rel"]
    html_file.parent.mkdir(parents=True, exist_ok=True)
    static_path = "../" * (len(html_file.relative_to(dist_dir).parents) - 1)

    detail_template.stream(
        **__detail_context(
            config,
            Path(source_dir) / article_record["md_rel"],
            source_dir,
            html_file,
            dist_dir,
            static_path,
            article_record["title"],
            article_record["tags"],
            article_record["toc"],
            article_record["html"],
        )
    ).dump(str(html_file), encoding="utf-8")

    __process_image(
        Path(source_dir) / article_record["md_rel"],
        source_dir,
        dist_dir,
        article_record["html"],
        str(html_file),
    )


def __records_to_listing(records, page_size):
    info = {}
    top_fix = []
    temp_info = []

    for record in records.values():
        item = (
            record["html_rel"],
            record["title"],
            record["pub_date"],
            UNKNOWN_READ_COUNT,
        )
        if record["pub_date"] == "":
            top_fix.append(item)
        else:
            temp_info.append(item)

    new_info = sorted(temp_info, key=lambda x: x[2], reverse=True)
    post_len = len(new_info)
    page_cnt = math.ceil(post_len / page_size) if post_len else 1
    for i in range(0, page_cnt):
        info[i] = new_info[i * page_size : min(i * page_size + page_size, post_len)]
    return info, top_fix


def __clean_index_pages(dist_dir):
    dist_path = Path(dist_dir)
    for page in dist_path.glob("index*.html"):
        page.unlink(missing_ok=True)


def __render_index_pages(index_template, config, dist_dir, records):
    page_size = config["page_size"]
    pagger_len = config["pagger_len"]
    pagegger_info, top_fix = __records_to_listing(records, page_size)
    total_page = len(pagegger_info.keys())

    __clean_index_pages(dist_dir)
    for idx, post_list in pagegger_info.items():
        if idx == 0:
            list_page = Path(dist_dir) / "index.html"
        else:
            list_page = Path(dist_dir) / f"index_{idx}.html"
        static_path = "../" * (len(list_page.relative_to(dist_dir).parents) - 1)

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
        ).dump(str(list_page), encoding="utf-8")


def __render_tag_pages(env, config, dist_dir, records):
    tags_article = {}
    for record in records.values():
        for tag in record["tags"]:
            tags_article.setdefault(tag, []).append(record["html_rel"])

    tag_template = env.get_template("tag.html")
    tag_dir = Path(dist_dir) / "tags"
    tag_dir.mkdir(parents=True, exist_ok=True)
    for old_page in tag_dir.glob("tag_*.html"):
        old_page.unlink(missing_ok=True)

    for tag, article_list in tags_article.items():
        new_article_list = [
            (f"../{html_rel}", Path(html_rel).stem, html_rel[0 : -len(Path(html_rel).name)])
            for html_rel in article_list
        ]
        tag_template.stream(
            post=new_article_list,
            **__shared_page_context(config, "../", title=f"分类_{tag}"),
        ).dump(str(tag_dir / f"tag_{tag}.html"), encoding="utf-8")


def __clean_output_assets_for_changed_dirs(source_dir, dist_dir, changed_assets):
    cleaned_dirs = set()
    for asset_path in changed_assets:
        parent = Path(asset_path).parent
        dir_name = __output_dir_name_for_source_relative(parent)
        if dir_name in cleaned_dirs:
            continue
        target_dir = Path(dist_dir) / dir_name
        if not target_dir.exists():
            continue
        for item in target_dir.iterdir():
            if item.is_file() and item.suffix.lower() != ".html":
                item.unlink(missing_ok=True)
            elif item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
        cleaned_dirs.add(dir_name)


def __article_from_manifest_entry(md_rel, manifest_entry):
    return {
        "md_rel": md_rel,
        "html_rel": manifest_entry["html_rel"],
        "title": manifest_entry["title"],
        "pub_date": manifest_entry["pub_date"],
        "tags": manifest_entry.get("tags", []),
    }


def __full_build(config, source_dir, dist_dir, env):
    __reset_dist_dir(dist_dir)
    detail_template = env.get_template("detail.html")
    index_template = env.get_template("index.html")
    md_2_html = __all_md_files(source_dir, dist_dir)

    records = {}
    for md, _html_file in md_2_html.items():
        article_record = __build_article_record(md, source_dir, dist_dir, config["markdown_extensions"])
        __render_article(detail_template, config, source_dir, dist_dir, article_record)
        records[article_record["md_rel"]] = {
            "html_rel": article_record["html_rel"],
            "title": article_record["title"],
            "pub_date": article_record["pub_date"],
            "tags": article_record["tags"],
        }

    __copy_resource(f"{config['template_dir']}/{config['theme']}", config["theme_static"], dist_dir)
    __render_index_pages(index_template, config, dist_dir, records)
    __render_tag_pages(env, config, dist_dir, records)
    __copy_cname(source_dir, dist_dir)
    __save_manifest(dist_dir, records)
    return "full"


def __incremental_build(config, source_dir, dist_dir, env, changed_files):
    classification = __classify_changed_files(changed_files, source_dir)
    if classification["mode"] == "full":
        print(f"fall back to full build: {classification['reason']}")
        return __full_build(config, source_dir, dist_dir, env)

    manifest = __load_manifest(dist_dir)
    old_records = manifest.get("posts", {})
    current_md_map = __all_md_files(source_dir, dist_dir)
    current_posts = {Path(md).relative_to(source_dir).as_posix(): md for md in current_md_map}

    changed_posts = set(classification["changed_posts"])
    changed_posts.update(set(old_records.keys()) - set(current_posts.keys()))
    changed_posts.update(set(current_posts.keys()) - set(old_records.keys()))

    detail_template = env.get_template("detail.html")
    index_template = env.get_template("index.html")
    new_records = {}

    __clean_output_assets_for_changed_dirs(source_dir, dist_dir, classification["changed_assets"])

    for md_rel, manifest_entry in old_records.items():
        if md_rel not in current_posts:
            old_html = Path(dist_dir) / manifest_entry["html_rel"]
            old_html.unlink(missing_ok=True)
            continue
        if md_rel not in changed_posts:
            new_records[md_rel] = manifest_entry

    for md_rel in sorted(changed_posts):
        if md_rel not in current_posts:
            continue
        article_record = __build_article_record(
            Path(source_dir) / md_rel,
            source_dir,
            dist_dir,
            config["markdown_extensions"],
        )
        __render_article(detail_template, config, source_dir, dist_dir, article_record)
        new_records[md_rel] = {
            "html_rel": article_record["html_rel"],
            "title": article_record["title"],
            "pub_date": article_record["pub_date"],
            "tags": article_record["tags"],
        }

    __copy_resource(f"{config['template_dir']}/{config['theme']}", config["theme_static"], dist_dir)
    __render_index_pages(index_template, config, dist_dir, new_records)
    __render_tag_pages(env, config, dist_dir, new_records)
    __copy_cname(source_dir, dist_dir)
    __save_manifest(dist_dir, new_records)
    return "incremental"


def build_site(source_dir, dist_dir, changed_files=None):
    config = __get_config("config.json")
    template_theme_dir = f"{config['template_dir']}/{config['theme']}"
    env = Environment(loader=FileSystemLoader(template_theme_dir))
    env.globals["build_version"] = datetime.now().strftime("%Y%m%d")

    Path(dist_dir).mkdir(parents=True, exist_ok=True)
    if changed_files:
        changed_paths = __read_changed_files(changed_files)
        if changed_paths:
            return __incremental_build(config, source_dir, dist_dir, env, changed_paths)
    return __full_build(config, source_dir, dist_dir, env)


def main(source_dir, dist_dir, changed_files=None):
    return build_site(source_dir, dist_dir, changed_files=changed_files)


if __name__ == "__main__":
    cur_dir = Path(__file__).parent
    print(cur_dir)
