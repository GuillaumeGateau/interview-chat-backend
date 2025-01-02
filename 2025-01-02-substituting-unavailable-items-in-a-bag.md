---
title: Substituting Unavailable Items in a Bag
jobId: Macy's
date: 2025-01-02T18:53:55.537Z
description: "Unavailable items using a substitutability index to recommend new
  products and remove frictions "
---
#### The Problem

Online shopping at scale is riddled with challenges, and I consistently saw one core issue at Macy's: customers adding items to their cart only to find them unavailable at checkout. This wasn’t just a technical hiccup; it was a customer experience failure. 

* Items disappearing from availability frustrated customers.
* Lack of transparency on why an item was no longer available caused confusion and eroded trust.
* Customers struggled to find suitable replacements quickly, stalling their journey to checkout.

The deeper issue? Managing inventory for thousands of SKUs across a vast geographic supply chain. A hot-selling item in one region might be out of stock in another. High-ticket items added another layer of complexity; without clear substitutions or incentives, they often sat in carts until abandoned.

#### The Solution

To fix this, I spearheaded a comprehensive solution with two key parts: the **Substitutability Index** and a set of machine learning-powered enhancements.

##### Substitutability Index

Before jumping into algorithms, I built the Substitutability Index. This framework provided a structured way to prioritize alternatives for unavailable items. We scored items on:

1. **Category Match**: Ensuring replacements stayed within the same category (e.g., handbags for handbags).
2. **Feature Similarity**: Matching critical attributes like size, style, and material.
3. **Regional Availability**: Leveraging supply chain data to ensure recommendations were actually in stock locally.
4. **Price Proximity**: Avoiding customer frustration by suggesting alternatives within a reasonable price range.

This index wasn’t just a planning tool; it became the foundation for how we trained our machine learning models.

##### Key Enhancements

1. **Real-Time Inventory Sync**

   * Integrated systems to monitor availability in real time.
   * Added instant notifications for customers when items became unavailable, paired with actionable next steps.
2. **Machine Learning for Substitution**

   * Built on the Substitutability Index to recommend replacements dynamically.
   * Factored in browsing patterns and past purchase behaviors to personalize results.
   * Adjusted recommendations based on regional availability to align with real-world inventory.
3. **Dynamic Cart Features**

   * Flagged unavailable items directly in the cart and highlighted promotional alternatives.
   * Designed intuitive interfaces to make replacement selection seamless.
4. **Supply Chain Data Integration**

   * Worked closely with supply chain teams to improve SKU tracking across regions.
   * Used predictive models to flag items likely to go out of stock and proactively suggested alternatives.
5. **Clear and Honest Communication**

   * Improved messaging to explain unavailability and build trust.
   * Highlighted reasons like regional stockouts, high demand, or limited editions.

#### Key Results

* **15% Boost in Conversion Rates**: Clear alternatives kept customers engaged and moving through checkout.
* **20% Drop in Cart Abandonment**: Transparency and seamless substitutions prevented frustration.
* **Better Inventory Turnover**: Substitution recommendations drove sales of slower-moving items.
* **Happier Customers**: Surveys showed increased trust and a more positive shopping experience.

#### Why It Matters

This wasn’t just about fixing one piece of the puzzle. It was about rethinking how we handle inventory at scale, build trust with customers, and recover lost sales. The Substitutability Index didn’t just solve the problem—it became a blueprint for how Macy’s could approach personalization and inventory management for years to come. We turned a frustrating process into a smoother, more intuitive experience, and that’s what keeps customers coming back.