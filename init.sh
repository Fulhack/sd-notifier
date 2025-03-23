git init -b main
git add .
git commit -m "init commit"
gh repo create fulhack/sd-notifier --source=. --remote=upstream
# git remote add origin git@github.com:mberglof/sd-notifier.git
git push -u origin main
