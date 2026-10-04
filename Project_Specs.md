# **INTRODUCTION TO INTELLIGENT SYSTEMS**

# **(Course Project Specification)**

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>Project Requirement(s)</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><p><strong>Network Guardian: Detecting Network Intrusions with Machine Learning</strong></p>
<p><img src="./media/media/image1.jpeg" style="width:4.51806in;height:2.27673in" alt="Intrusion Detection System (IDS) and Its detailed Function – SOC/SIEM" /></p>
<p>A company's security team watches thousands of network connections every minute. Most are ordinary: employees browsing, servers talking to each other, files moving around. Hidden among them are a few connections made by attackers. No human can inspect every connection, and the team keeps missing real threats while chasing false alarms.</p>
<p>Your team have been hired as a junior data science team to build the prototype of an Intrusion Detection System (IDS): a program that looks at the description of a network connection and decides whether it is normal or an attack, and if it is an attack, what kind.</p>
<p><strong>Project Objectives</strong></p>
<p>Build, test, and compare machine learning classifiers that can tell normal connections from attacks, and recommend which approach the company should trust. Then explain your work and your reasoning in a video presentation.</p>
<p>By the end of this project, you should be able to:</p>
<ol type="1">
<li><p>Explore an unfamiliar dataset and describe what it contains and what might go wrong with it.</p></li>
<li><p>Decide how data must be prepared for machine learning and justify each decision.</p></li>
<li><p>Train and compare several classification approaches fairly.</p></li>
<li><p>Choose evaluation measures that fit the real-world problem and interpret them critically.</p></li>
<li><p>Communicate technical findings clearly to an audience through video.</p></li>
</ol>
<p><strong>Guide Questions</strong></p>
<p>These are prompts for discovery. They are not instructions, and you are not expected to answer all of them in this order. Some may lead you to ask better questions of your own.</p>
<ul>
<li><p>Look at your data before doing anything else. What surprises you? What would worry you?</p></li>
<li><p>Can a computer use every column exactly as it is? Why or why not?</p></li>
<li><p>Do all the classes appear equally often? Would that matter for what a model learns?</p></li>
<li><p>Are all features equally useful? Might some be redundant, or useless? How could you find out?</p></li>
<li><p>How will you know whether a model works on connections it has never seen?</p></li>
<li><p>Is a high accuracy score enough to call a model good? Who gets hurt if the model is wrong, and in which direction?</p></li>
<li><p>Why might one model learn quickly and another slowly? Does speed matter for a real IDS?</p></li>
<li><p>If a model looks perfect, should you be happy or suspicious?</p></li>
</ul>
<p><strong>Implementation Requirement</strong></p>
<ul>
<li><p>Work in Python using a Jupyter or Google Colab notebook. Libraries such as pandas, NumPy, scikit-learn, Matplotlib, and Seaborn are allowed.</p></li>
<li><p>Build and compare at least three different classification approaches of your own choosing.</p></li>
<li><p>Your models must predict the connection category (normal or one of the attack families).</p></li>
<li><p>Your results must be reproducible: fix any random settings so that your teacher gets the same results when running your notebook.</p></li>
<li><p>Every decision must be explained in your notebook in your own words, using text cells.</p></li>
</ul>
<p><strong>Academic Honesty</strong></p>
<p>You may consult documentation, tutorials, and other resources, but you must cite them. Copying a published solution, or using an AI assistant without disclosing it, is not allowed. Every member must be able to explain any line of code in the submission.</p>
<p><strong>Documentation Requirement</strong></p>
<p>Cover Page</p>
<p>Table of Contents</p>
<ol type="1">
<li><p><strong>Introduction</strong></p></li>
</ol>
<blockquote>
<p><em>Provide a brief description of the Network Guardian project, including its purpose and the problem it aims to address.</em></p>
</blockquote>
<ol start="2" type="1">
<li><p><strong>Dataset Understanding and Preparation</strong></p></li>
</ol>
<blockquote>
<p><em>Document the team’s process of understanding and preparing the provided dataset for machine learning.</em></p>
</blockquote>
<ol start="3" type="1">
<li><p><strong>Machine Learning Model Development</strong></p></li>
</ol>
<blockquote>
<p><em>Document the machine learning models developed for the Network Guardian system.</em></p>
</blockquote>
<ol start="4" type="1">
<li><p><strong>Model Metadata</strong></p></li>
</ol>
<blockquote>
<p><em>Provide the metadata of the machine learning models developed and compared in the project.</em></p>
</blockquote>
<ol start="5" type="1">
<li><p><strong>Model Comparison and Evaluation</strong></p></li>
</ol>
<blockquote>
<p><em>Present the evaluation and comparison of the machine learning models.</em></p>
</blockquote>
<ol start="6" type="1">
<li><p><strong>Results and Visualizations</strong></p></li>
</ol>
<blockquote>
<p><em>Present the major results and visualizations generated throughout the project.</em></p>
</blockquote>
<ol start="7" type="1">
<li><p><strong>Discovery Log</strong></p></li>
</ol>
<blockquote>
<p><em>Provide the team's Discovery Log documenting the development and investigation process.</em></p>
</blockquote>
<ol start="8" type="1">
<li><p><strong>Executive Summary</strong></p></li>
</ol>
<blockquote>
<p><em>Provide a concise executive summary written for a reader who has not reviewed the complete notebook.</em></p>
</blockquote>
<ol start="9" type="1">
<li><p><strong>Reflection (Individual)</strong></p></li>
</ol>
<blockquote>
<p><em>Each team member must provide an individual reflection discussing their experience in developing the Network Guardian project.</em></p>
</blockquote>
<ol start="10" type="1">
<li><p><strong>References</strong></p></li>
</ol>
<blockquote>
<p><em>Provide all references used throughout the project.</em></p>
</blockquote>
<p><strong>Video Presentation Requirements</strong></p>
<p>Be able to deliver a video presentation of the overall Network Guardian course project implementation, highlighting the project problem and its significance, initial findings from the provided dataset, data preparation process, machine learning approaches developed, model comparison and evaluation, key results and visualizations, model recommendation and supporting evidence, project limitations, challenges and wrong turns encountered during development, and the team's learning and reflection throughout the project.</p>
<p>Your video should cover the following, in whatever order tells your story best:</p>
<ul>
<li><p>The problem and why it matters.</p></li>
<li><p>What you found when you first looked at the data.</p></li>
<li><p>How you approached the work, including the wrong turns and what they taught you.</p></li>
<li><p>How your models compare, and how you judged them.</p></li>
<li><p>Your recommendation to the company, and the limitations of your work.</p></li>
<li><p>A short reflection on what you learned and how your team worked together.</p></li>
</ul>
<p>Note: Every member must appear (on-cam) and speak</p>
<p><strong>Submission Requirements</strong></p>
<p>Final Documentation (Printed Copy and Softcopy in PDF)</p>
<p>Course Project Rubrics (Printed Copy)</p>
<p>Video Presentation (MP4; 5-8 minutes)</p></td>
</tr>
</tbody>
</table>

# **INTRODUCTION TO INTELLIGENT SYSTEMS**

# **(Course Project Rubrics)**

| **Term / Academic Year** | ***T1 AY 2026-2027***                      | **Date**    | October 1, 2026            |
|--------------------------|--------------------------------------------|-------------|----------------------------|
| **Group Name**           | Click or tap here to enter text.           |             |                            |
| **Members**              | **Surname, First Name MI. (Alphabetical)** | **Section** | **Program Specialization** |
|                          | Click or tap here to enter text.           |             | Choose an item.            |
|                          | Click or tap here to enter text.           |             | Choose an item.            |
|                          | Click or tap here to enter text.           |             | Choose an item.            |
|                          | Click or tap here to enter text.           |             | Choose an item.            |
|                          | Click or tap here to enter text.           |             | Choose an item.            |

<table>
<colgroup>
<col style="width: 13%" />
<col style="width: 2%" />
<col style="width: 2%" />
<col style="width: 3%" />
<col style="width: 12%" />
<col style="width: 15%" />
<col style="width: 15%" />
<col style="width: 14%" />
<col style="width: 15%" />
<col style="width: 5%" />
</colgroup>
<thead>
<tr class="header">
<th><p><strong>Project</strong></p>
<p><strong>Component</strong></p></th>
<th colspan="2"><blockquote>
<p><strong>SO</strong></p>
</blockquote></th>
<th colspan="2"><p><strong>Unsatisfactory</strong></p>
<p><strong>(0)</strong></p></th>
<th><p><strong>Needs</strong></p>
<p><strong>Improvement</strong></p>
<p><strong>(1)</strong></p></th>
<th><p><strong>Satisfactory</strong></p>
<p><strong>(2)</strong></p></th>
<th><p><strong>Proficient</strong></p>
<p><strong>(3)</strong></p></th>
<th><p><strong>Exceptional</strong></p>
<p><strong>(4)</strong></p></th>
<th><strong>PTS</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><strong>Data Understanding and Preparation</strong></td>
<td colspan="2" rowspan="5"><blockquote>
<p>SO5</p>
</blockquote></td>
<td colspan="2"><blockquote>
<p>No evidence of exploration or preparation.</p>
</blockquote></td>
<td><blockquote>
<p>Minimal exploration. Preparation is incomplete, incorrect or unexplained.</p>
</blockquote></td>
<td><blockquote>
<p>Basic exploration with few insights. Preparation is done but with little justification, or with minor errors.</p>
</blockquote></td>
<td><blockquote>
<p>Explores the data well and identifies most key patterns and problems. Most preparation decisions are justified.</p>
</blockquote></td>
<td><blockquote>
<p>Explores the data thoroughly and supports findings with evidence or visuals. Identifies problems in the data and justifies every preparation decision, including its effect on results.</p>
</blockquote></td>
<td></td>
</tr>
<tr class="even">
<td><strong>Model Building and Comparison</strong></td>
<td colspan="2"><blockquote>
<p>No working model.</p>
</blockquote></td>
<td><blockquote>
<p>One working model only, or models are barely functional.</p>
</blockquote></td>
<td><blockquote>
<p>Builds fewer than three models, or the comparison is unfair or unclear.</p>
</blockquote></td>
<td><blockquote>
<p>Builds at least three models with some exploration of settings. Comparison is mostly fair and clear.</p>
</blockquote></td>
<td><blockquote>
<p>Builds several well-chosen models from different approaches. Explores settings deliberately and compares models fairly under the same conditions.</p>
</blockquote></td>
<td></td>
</tr>
<tr class="odd">
<td><strong>Evaluation and Interpretation</strong></td>
<td colspan="2"><blockquote>
<p>No evaluation or recommendation.</p>
</blockquote></td>
<td><blockquote>
<p>Evaluation is misleading or superficial. Recommendation is unsupported.</p>
</blockquote></td>
<td><blockquote>
<p>Relies mostly on one measure. Interpretation and recommendation are vague or weakly supported.</p>
</blockquote></td>
<td><blockquote>
<p>Uses appropriate measures, considers overfitting and errors, and gives a sound recommendation with limitations noted.</p>
</blockquote></td>
<td><blockquote>
<p>Uses measures suited to the problem and looks beyond a single number. Reasons about the real cost of different errors and checks for overfitting. Gives a clear, evidence-based recommendation with honest limitations.</p>
</blockquote></td>
<td></td>
</tr>
<tr class="even">
<td><strong>Discovery Process and Documentation</strong></td>
<td colspan="2"><blockquote>
<p>Notebook, log, metadata and summary missing, or work copied without attribution.</p>
</blockquote></td>
<td><blockquote>
<p>Notebook is hard to follow or does not run fully. Log is very brief. Metadata or summary mostly missing or unclear. Originality is doubtful.</p>
</blockquote></td>
<td><blockquote>
<p>Notebook needs fixes or is sparsely commented. Log lists results with little reflection. Metadata or summary partly complete. Citations incomplete.</p>
</blockquote></td>
<td><blockquote>
<p>Notebook runs with minor issues and is well organized. Log is complete and reflective. Metadata and summary are complete with minor gaps. Sources cited.</p>
</blockquote></td>
<td><blockquote>
<p>Notebook runs fully, is clean, commented and reproducible. Discovery Log honestly records questions, failures and lessons. Metadata is complete and accurate; Executive Summary answers all six questions clearly and concisely. Work is original and sources are cited.</p>
</blockquote></td>
<td></td>
</tr>
<tr class="odd">
<td><strong>Presentation</strong></td>
<td colspan="2"><blockquote>
<p>No video submitted.</p>
</blockquote></td>
<td><blockquote>
<p>Incomplete or inaccurate content, disorganized delivery, poor audio or visuals, several requirements missed.</p>
</blockquote></td>
<td><blockquote>
<p>Surface-level explanation, uneven flow, or some members silent. Audio or visuals sometimes hard to follow. Misses some requirements.</p>
</blockquote></td>
<td><blockquote>
<p>Mostly accurate explanation with good flow. All members speak. Good audio and visuals. Meets most requirements and includes a reflection.</p>
</blockquote></td>
<td><blockquote>
<p>Accurate, in-depth explanation of the problem, process, findings and recommendation, including the discovery journey. Clear flow, every member speaks confidently, strong visuals and audio, within the time limit, with a thoughtful reflection.</p>
</blockquote></td>
<td></td>
</tr>
<tr class="even">
<td colspan="8"><strong>Total Score and Feedback</strong></td>
<td rowspan="6"><strong>TOTAL POINTS EARNED</strong></td>
<td rowspan="6"></td>
</tr>
<tr class="odd">
<td colspan="2">☐ Exceptional</td>
<td colspan="2">20</td>
<td colspan="4"><blockquote>
<p>Outstanding performance in all project components with minimal to no issues</p>
</blockquote></td>
</tr>
<tr class="even">
<td colspan="2">☐ Proficient</td>
<td colspan="2">16-19</td>
<td colspan="4"><blockquote>
<p>Good performance in most project components with minor issues.</p>
</blockquote></td>
</tr>
<tr class="odd">
<td colspan="2">☐ Satisfactory</td>
<td colspan="2">12-15</td>
<td colspan="4"><blockquote>
<p>Acceptable performance in basic aspects with several issues.</p>
</blockquote></td>
</tr>
<tr class="even">
<td colspan="2">☐ Needs Improvement</td>
<td colspan="2">8-11</td>
<td colspan="4"><blockquote>
<p>Below-average performance with many issues.</p>
</blockquote></td>
</tr>
<tr class="odd">
<td colspan="2">☐ Unsatisfactory</td>
<td colspan="2">0-7</td>
<td colspan="4"><blockquote>
<p>Poor performance with critical issues in most project components.</p>
</blockquote></td>
</tr>
<tr class="even">
<td colspan="4"><p>Evaluated by:</p>
<p>_______________________</p>
<p>Name of Course Instructor/Date</p></td>
<td colspan="4"><blockquote>
<p><strong>Remarks/Comments</strong></p>
</blockquote></td>
<td></td>
<td></td>
</tr>
</tbody>
</table>

# 

# **INTRODUCTION TO INTELLIGENT SYSTEMS**

# **(Peer/Self Evaluation Rubrics)**

<table>
<colgroup>
<col style="width: 18%" />
<col style="width: 6%" />
<col style="width: 8%" />
<col style="width: 18%" />
<col style="width: 14%" />
<col style="width: 11%" />
<col style="width: 16%" />
<col style="width: 5%" />
</colgroup>
<thead>
<tr class="header">
<th rowspan="3"><p><strong>Student Name(s)</strong></p>
<p><em>All members including the evaluator.</em></p></th>
<th colspan="2"><strong>Contribution to Team Effort</strong></th>
<th><blockquote>
<p><strong>Communication</strong></p>
</blockquote>
<p><strong>Skills</strong></p></th>
<th><p><strong>Meeting</strong></p>
<p><strong>Deadlines and Reliability</strong></p></th>
<th><blockquote>
<p><strong>Quality of Work</strong></p>
</blockquote></th>
<th><strong>Collaboration and Teamwork</strong></th>
<th rowspan="3"><strong>PTS</strong></th>
</tr>
<tr class="odd">
<th colspan="2">Contributes meaningfully to group discussions.</th>
<th><blockquote>
<p>Demonstrate excellence in written and verbal</p>
</blockquote>
<p>communication skills</p></th>
<th>Completes group assigned task(s) on time.</th>
<th>Prepares work in a quality manner</th>
<th>Demonstrate a cooperative and supportive attitude.</th>
</tr>
<tr class="header">
<th colspan="6">Using scale 0-4 (0=Unsatisfactory; 1=Needs Improvement; 2=Satisfactory; 3=Proficient; 4=Exceptional)</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td></td>
<td colspan="2"></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
<tr class="even">
<td></td>
<td colspan="2"></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
<tr class="odd">
<td></td>
<td colspan="2"></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
<tr class="even">
<td></td>
<td colspan="2"></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
<tr class="odd">
<td></td>
<td colspan="2"></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
<tr class="even">
<td></td>
<td colspan="6"><blockquote>
<p><strong>Peer Evaluation Interpretation</strong></p>
</blockquote></td>
<td></td>
</tr>
<tr class="odd">
<td>☐ Exceptional</td>
<td>20</td>
<td colspan="5"><blockquote>
<p>Outstanding performance across all indicators.</p>
</blockquote></td>
<td></td>
</tr>
<tr class="even">
<td>☐ Proficient</td>
<td>16-19</td>
<td colspan="5"><blockquote>
<p>Strong performance with minor areas for improvement.</p>
</blockquote></td>
<td></td>
</tr>
<tr class="odd">
<td>☐ Satisfactory</td>
<td>12-15</td>
<td colspan="5"><blockquote>
<p>Adequate performance with several areas for improvement.</p>
</blockquote></td>
<td></td>
</tr>
<tr class="even">
<td>☐ Needs Improvement</td>
<td>8-11</td>
<td colspan="5"><blockquote>
<p>Below-average performance with significant areas for improvement.</p>
</blockquote></td>
<td></td>
</tr>
<tr class="odd">
<td>☐ Unsatisfactory</td>
<td>0-7</td>
<td colspan="5"><blockquote>
<p>Poor performance across most or all indicators.</p>
</blockquote></td>
<td></td>
</tr>
<tr class="even">
<td><strong>Remarks/Comments</strong></td>
<td colspan="6"></td>
<td></td>
</tr>
</tbody>
</table>
