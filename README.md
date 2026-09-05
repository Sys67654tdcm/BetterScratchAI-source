This is the source for [BetterScratchAI](https://scratch.mit.edu/users/BetterScratchAI) - my Scratch bot.
This requires Ollama (not the Python module, the app) running in the background.

`cfg.json` should be formatted like this:

```json
{
  "pid": 123456789,
  "ids": "replied_ids.json",
  "model": "qwen2.5:1.5b",
  "username": "USERNAME_HERE",
  "password": "PASSWORD_HERE",
  "hoster": "HOSTER_USERNAME_HERE",
  "ppm": 1
}
```
where `"pid"` is the project ID it is commenting on (by the bot's account),
`"ids"` is the IDs file where replied IDs are stored,
`"model"` is the model that is currently running on Ollama,
`"username"` is the bot's account's username,
`"password"` is the bot's account's password,
`"hoster"` is the hoster's account's username,
`"max_ids"` is the maximum amount of IDs stored,
and `"ppm"` is the amount of Polls Per Minute. (thats what PPM stands for here)
If `"max_ids"` goes over 40, it will automatically go down to 40.

Please Note: This requires `scratchattach`.
