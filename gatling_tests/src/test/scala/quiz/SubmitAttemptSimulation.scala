package quiz

import io.gatling.core.Predef._
import io.gatling.http.Predef._
import scala.concurrent.duration._

class SubmitAttemptSimulation extends Simulation {

  // 1. HTTP Configuration
  val httpProtocol = http
    .baseUrl("http://localhost:8000/api/v1")
    .acceptHeader("application/json")
    .contentTypeHeader("application/json")

  // 2. Load the CSV feeder containing pre-generated tokens and attempt details
  // Note: users.csv is created by our Python setup script.
  val userFeeder = csv("feeders/users.csv").circular

  // 3. Define the Scenario
  val submitAttemptScenario = scenario("Submit Quiz Attempt")
    .feed(userFeeder)
    .exec(
      http("Submit Attempt")
        .post("/attempts/${attempt_id}/submit")
        .header("Authorization", "Bearer ${token}")
        .body(StringBody(
          """{
            |  "answers": [
            |    {
            |      "question_id": "${question_id}",
            |      "selected_option_id": "${option_id}"
            |    }
            |  ]
            |}""".stripMargin)).asJson
        .check(status.is(200))
    )

  // 4. Setup Load Profile
  setUp(
    submitAttemptScenario.inject(
      // Ramp up 50 users over 10 seconds to simulate moderate concurrent load
      rampUsers(50).during(10.seconds)
    )
  ).protocols(httpProtocol)
}
