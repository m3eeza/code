/*
 * Copyright (c) 2017 Uber Technologies, Inc.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */

package examples

import java.io._
import java.sql.{DriverManager, ResultSet}
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

import com.uber.engsec.dp.schema.Schema
import com.uber.engsec.dp.util.ElasticSensitivity

import scala.io.Source
import scala.util.parsing.json.JSON

/** A simple differential privacy example using elastic sensitivity.
  *
  * This example code supports queries that return a single column and single row. The code can be extended to support
  * queries returning multiple columns and rows by generating independent noise samples for each cell based the
  * appropriate column sensitivity.
  *
  * Caveats:
  *
  * Histogram queries (using SQL's GROUP BY) must be handled carefully so as not to leak information in the bin labels.
  * The analysis throws an error to warn about this, but this behavior can overridden if you know what you're doing.
  *
  * This example does not implement a privacy budget management strategy. Each query is executed using the full budget
  * value of EPSILON. Correct use of differential privacy requires allocating a fixed privacy from which a portion is
  * depleted to run each query. A privacy budget strategy depends on the problem domain and threat model and is
  * therefore beyond the scope of this tool.
  */
object ElasticSensitivityExample extends App {
  // Use the table schemas and metadata defined by the test classes
  System.setProperty("schema.config.path", "src/test/resources/schema.yaml")

  //Enter the database name
  val database = Schema.getDatabase("<Give database name here from schema>")

  // query result when executed on the database
  var QUERY_RESULT = 0.0

  // variable to store JSON string extracted from the file
  var jsonStr = ""

  // variable to count number of JSON files in the directory
  var fileCount = 0

  // path where JSON files are created by simpleServer.py
  val path: String = "<Enter path here>\\sql-differential-privacy\\src\\main\\scala\\examples\\"

  // timer to check the directory for new files periodically
  val t = new java.util.Timer()
  val task = new java.util.TimerTask {
    def run() = {

      // count the number of files with .json extension in the directory
      val tempFileCount = Option(new File(path).list).map(_.filter(_.endsWith(".json")).size).getOrElse(0)

      // if there is a new file created then get the file name
      if (tempFileCount != fileCount) {
        fileCount = tempFileCount
        var lastFileCreated = new File(path).list()(tempFileCount - 1)

        // append filename to the filepath
        val filename: String = path + lastFileCreated


        // read file to process JSON String
        for (line <- Source.fromFile(filename).getLines) {
          jsonStr = line;
        }


        // extract the query from the JSON
        val resultOption = JSON.parseFull(jsonStr) match {
          case Some(map: Map[String, String]) => map.get("query")
          case _ => None
        }
        val query = resultOption.get;

        // create connection to database
        classOf[org.postgresql.Driver]

        // enter appropriate credentials to connect to server
        val con_str = "jdbc:postgresql://db001.gda_score.org:5432/<database_name>?user=<username>&password=<password>"

        val conn = DriverManager.getConnection(con_str)

        // run extracted query on the database to get private result
        try {
          val stm = conn.createStatement(ResultSet.TYPE_FORWARD_ONLY, ResultSet.CONCUR_READ_ONLY)
          val rs = stm.executeQuery(query)

          while (rs.next) {

            // query result when executed on the database
            QUERY_RESULT = rs.getString(1).toDouble;

          }
        } finally {
          conn.close()
        }

        // privacy budget
        val EPSILON = 0.1
        // delta parameter: use 1/n^2, with n = 100000
        val DELTA = 1 / (math.pow(100000, 2))


        println(s"Query sent by client: " + query);
        println(s"Private result: $QUERY_RESULT\n")

        // get noisy result
        val noisyResult = ElasticSensitivity.addNoise(query, database, QUERY_RESULT, EPSILON, DELTA)
        println(s"Noisy result: %.0f".format(noisyResult))

        // FileWriter
        new PrintWriter("result" + LocalDateTime.now.format(DateTimeFormatter.ofPattern("YYYY-MM-dd_HH-mm-ss")) + ".txt") {
          write(noisyResult.toString); close
        }
        println("File Created!")


      }
    }
  }
  t.schedule(task, 100L, 100L)
  task.run()

}
