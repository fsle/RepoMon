import requests
import json
import os
import base64


with open(os.path.join(os.path.dirname(__file__),'config.json'), 'r') as config_file:
    config = json.load(config_file)

with open(os.path.join(os.path.dirname(__file__),'data.json'), 'r') as data_file:
    data = json.load(data_file)

def tg_notify(msg):
    print(msg)
    #espace markdown chars (they are a few more but we are not supposed to use them)
    msg = msg.replace('.' ,r"\.")
    msg = msg.replace('-' ,r"\-")
    msg = msg.replace('_' ,r"\_")
    msg = msg.replace('+' ,r"\+")
    msg = msg.replace('=' ,r"\=")
    msg = msg.replace('(' ,r"\(")
    msg = msg.replace(')' ,r"\)")
    url = f"https://api.telegram.org/bot{config['tg_token']}/sendMessage?chat_id={config['tg_chat_id']}&text={msg}&parse_mode=MarkdownV2"
    r = requests.get(url)
    if r.status_code != 200:
        tmp = base64.b64encode(msg.encode('utf-8')) #for dbg prupose
        url = f"https://api.telegram.org/bot{config['tg_token']}/sendMessage?chat_id={config['tg_chat_id']}&text={tmp}&parse_mode=MarkdownV2"
        requests.get(url)


def get_latest_tree(repo_config):
    api_url = f"https://api.github.com/repos/{repo_config['repo']}/git/trees/{repo_config['branch']}?recursive=1"
    headers = {
        'Authorization': f"token {config['github_token']}"
    }
    response = requests.get(api_url, headers=headers)
    response.raise_for_status()
    latest_tree = response.json()

    entries = {}
    for entry in latest_tree["tree"]:
        #handle files (not dir nor commits)
        if entry['type'] == "blob":
            #handle filters
            #include list
            if len(repo_config['filters']['include']) != 0:
                if entry['path'].startswith(tuple(repo_config['filters']['include'])):
                    entries[entry['path']] = entry['sha']
                continue

            #exclude list
            if len(repo_config['filters']['exclude']) != 0 and entry['path'].startswith(tuple(repo_config['filters']['exclude'])):
                continue
            entries[entry['path']] = entry['sha']
    return entries

def update_data(repo, last_commit, new_entries):
    data["repositories_data"][repo] = {
                "last_commit": last_commit,
                "entries": new_entries
            }
    save_data(data)


def check_diff(repo_config, last_commit, entries, saved):
    repo = repo_config["repo"]
    branch = repo_config["branch"]
    for (entry, sha) in entries.items():
        #new file
        if entry not in saved.keys():
            saved[entry] = sha
            update_data(repo, last_commit, saved)
            msg = rf"\[{repo}\] 🟢New file🟢 👉 [{entry}](https://github.com/{repo}/blob/{branch}/{entry})"
            tg_notify(msg)
        #updated file
        elif sha != saved[entry]:
            saved[entry] = sha
            update_data(repo, last_commit, saved)
            msg = rf"\[{repo}\] 🟠Updated file🟠 👉 [{entry}](https://github.com/{repo}/blob/{branch}/{entry})"
            tg_notify(msg)
    to_del = []
    for (entry, sha) in saved.items():
        #deleted file
        if entry not in entries.keys():
            to_del.append(entry)
            msg = rf"\[{repo}\]🔴Deleted file🔴 👉 [{entry}](https://github.com/{repo}/blob/{branch}/{entry})"
            tg_notify(msg)
    for el in to_del:
        del saved[el]
    
    #update for deletion but also the last_commit changes are not monitored
    update_data(repo, last_commit, saved)

def save_data(data):
    with open(os.path.join(os.path.dirname(__file__),'data.json'), 'w') as json_file:
            json.dump(data, json_file, indent=4)

def get_last_commit(repo, branch):
    api_url = f"https://api.github.com/repos/{repo}/commits/{branch}"
    headers = {
        'Authorization': f"token {config['github_token']}"
    }
    response = requests.get(api_url, headers=headers)
    response.raise_for_status()
    return response.json()['sha']


def check_repos():
    # Start monitoring all repositories from the configuration
    for repo_config in config['repositories']:
        repo = repo_config["repo"]

        print(f"[{repo}]")
        last_commit = get_last_commit(repo, repo_config['branch'])

        #first run
        if repo not in data["repositories_data"].keys():
            print("[initializing data.json for this repo]")
            update_data(repo_config["repo"], last_commit, get_latest_tree(repo_config))
            continue
        
        #check diffs
        if data["repositories_data"][repo]["last_commit"] != last_commit:
            entries = get_latest_tree(repo_config)
            check_diff(repo_config, last_commit, entries, data["repositories_data"][repo]["entries"])
        else:
            print("[nodiff]")
    


if __name__ == '__main__':
    check_repos()