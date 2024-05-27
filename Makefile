.PHONY: init all test

all:
	@ python3 ./sample/lion_bot.py

init:
	mkdir -p config
	mkdir -p logs
	touch logs/bot.log
	if [ ! -e ./logs/activity.log ]; then \
		echo {} > ./logs/activity.log; \
	fi
	touch logs/activity.log
	conda install --yes --file requirements.txt
