---
title: "Power Platform IndiePubs: Sending badges from Badgr to a Slack channel"
author: Troy Taylor
date: 2021-02-11
category: Power Platform
layout: post
---

I recently learned about [Badgr](https://badgr.com/) from one of the speakers at our recent internal Power Platform session. This is a service for issuing and managing digital badges. I started looking at it from a use case: what badges would I want to create for my own professional development and what would make sense for low code enthusiasts.

And then I thought if I could create a Power Automate flow that sent messages to a Slack channel, perhaps I could automate the sharing of any newly created badges in Badgr to Slack.

I created a Badgr custom connector from their Swagger files and after fixing the errors from the import, I created a new scheduled flow. Since the Badgr connector only has actions, I needed to determine a time interval to get all of the latest badges. I decided on a weekly Recurrence trigger. 

Then I added a new **Get All Assertions** action from the Badgr connector and used the following dynamic expression to get all badges issued in the last 7 days:

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1613063649063/2NU43MLKF.png)

This used the badge result and output a list I could use. Using an HTML table, I created a table that formatted the important fields from the Badgr data.

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1613064026929/6sNfWRB02.png)

Finally, the HTTP action to send that data to Slack.

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1613064181370/2mXnrp3vP.png)

I'm using the entire body of the table, but you can also use a compose action to add additional text above or below the table. I'm then using the body of the HTTP action in a Condition.

![image.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1613064311994/U6HCkMu0B.png)

If the status code is 200, it was successful. Otherwise, I'm sending myself a notification.
