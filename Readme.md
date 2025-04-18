
## RepoMon

### Why?

Idea comes from [that tweet](https://x.com/SoSoValue/status/1910518663893180888).
```
We’re excited to share that SSI has officially completed all smart contract audits, with reports delivered by top security firms including: 
@BlockSecTeam, @SlowMist_Team, @zenith256, @TenArmor, @zellic_io, and @Quantstamp.
```

Detailed chronology [here](https://sosovalue-white-paper.gitbook.io/sosovalue-whitepaper/9.-resources/9.2-audits).

### What?

It populates a json which represents all the monitord files in repositories.

The tool should be launched regularly to monitor any diff (new, updated or deleted files).

Currently sends a notification message to a telegram channel when a update is detected.


### Install
- install dependency
```
pip3 install requests
```
- modify `config.json.sample` and copy to `config.json`
    - "github_token": github token to avoid being rate limited when listing files in repositories.
    - "tg_token": telegram token of the telegram bot that will send the message.
    -  "tg_chat_id": chat id where the notification will be sent.
- crontab (launches the script every 10 minutes)
```
*/10 * * * * exec /usr/bin/python3 /home/path/to/RepoMon/RepoMon.py
```