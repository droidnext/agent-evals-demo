Feature: Search and Book Flow (temp example)
  User searches for a cruise, narrows options, asks pricing, drills into itinerary,
  then asks about cabins and booking. Mirrors temp/search_and_book.json turn-for-turn.

  Scenario: Turn 1 — list destinations
    When the user sends this message:
      """
      I'm looking for a cruise vacation. What destinations do you have?
      """
    Then the agent behavior should match:
      """
      Agent should list available cruise destinations or regions (e.g., Caribbean, Mediterranean, Alaska) and invite the user to narrow their search.
      """
    And required tools include:
      | tool           |
      | search_cruises |

  Scenario: Turn 2 — search from Miami, 7 days
    Given structured user parameters:
      | field           | value |
      | duration_days   | 7     |
      | departure_port  | Miami |
    When the user sends this message:
      """
      Show me 7-day cruises from Miami
      """
    Then the agent behavior should match:
      """
      Agent should route to the search sub-agent and return cruise options departing from Miami with approximately 7-day durations. Results should include ship names, dates, or itinerary highlights.
      """
    And required tools include:
      | tool           |
      | search_cruises |
    And total tool invocations must not exceed 5

  Scenario: Turn 3 — price range for prior options
    When the user sends this message:
      """
      What's the price range for those options?
      """
    Then the agent behavior should match:
      """
      Agent should reference the cruises from the previous turn and provide pricing information via the pricing sub-agent. Should not ask the user to re-specify which cruises.
      """
    And required tools include:
      | tool             |
      | get_pricing_info |

  Scenario: Turn 4 — cheapest option ports
    Given conversation context note:
      """
      User is referring to the lowest-priced cruise from the previous pricing response.
      """
    When the user sends this message:
      """
      Tell me more about the cheapest option — what ports does it visit?
      """
    Then the agent behavior should match:
      """
      Agent should identify the lowest-priced cruise from the prior turn, then provide itinerary details including port stops via the itinerary sub-agent. Should maintain context from earlier pricing results.
      """
    And required tools include:
      | tool             |
      | get_cruise_by_id |

  Scenario: Turn 5 — cabin types and booking
    When the user sends this message:
      """
      That sounds great. What cabin types are available and how do I book?
      """
    Then the agent behavior should match:
      """
      Agent should list the available cabin types (e.g., Interior, Oceanview, Balcony, Suite) with their per-person prices for the selected cruise, and offer to connect the user with a human agent for booking assistance.
      """
    And required tools include:
      | tool             |
      | get_pricing_info |
