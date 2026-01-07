---
title: "Power Platform IndiePubs: Adding leads to Dynamics 365 from HubSpot in real-time"
author: Troy Taylor
date: 2021-02-23
category: Power Platform
layout: post
---

At the recent MVP meetup (thanks again Matt Beard), Brian Knight ([@BrianKnight](https://twitter.com/BrianKnight)) asked for solutions to sync HubSpot leads to Dynamics 365 in real-time. After looking at the out-of-the-box HubSpot connector and the Common Data Service connector, I had a basic proof-of-concept in about 20 minutes, mostly because the schema responses are different between the two services. The flow was quite simple:

- When a lead is created or updated in HubSpot, use it as a trigger
- Use a get lead action to pull the details of that lead
- Parse the JSON response
- Use a switch to decide if the lead exists in D365
- Add a case for the lead to be added
- Add a case for the lead to be updated
- Test and test again.

I recently discovered a [YouTube channel](https://www.youtube.com/channel/UChVuMhgWWOO68DRGnz2qwrQ) by Reza Dorrani who does videos about Power Automate with some coverage of Azure Logic Apps. I recommend checking him out if you are wanting to learn about custom connectors with Azure AD auth.

He recently did [a video](https://www.youtube.com/watch?v=c0J5Zxg3ltU) on adding rows to Excel in batches (an action with a 10,000-row limit) and shows how you can then use the compose action to iterate through a set of variables and produce a working batch. I loved the concept, and I had other custom connectors on my mind to work on so I decided to convert my proof-of-concept to a blog post.

Two days later, I had the flow fully built and documented with plenty of screenshots in a [blog post on Hashnode](https://troystaylor.hashnode.dev/power-platform-indiepubs-adding-leads-to-dynamics-365-from-hubspot-in-real-time).

After re-reading that flow for the fifth time, I still think it could be improved. I notice I use a lot of words trying to explain my thinking.
