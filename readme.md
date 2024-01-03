
- ## ArgSys options and flags:
    Select Tests (by tags coded in suites and tests with @TAG, @NAME, @LEVEL, @FEATURES)
    #### options (excludes have higher importance over includes):
        -ip         Include Package (ex: -is qa.regression -es qa.regression.dev), can be several
        -ep         Exclude Package
        -is         Include Suite (ex: -is suiteCertificates -is MICROSERVICES -es DEV), can be several
        -es         Exclude Suite
        -it         Include Test (ex: -it REST), can be several
        -et         Exclude Test
        -sb         filename of the StoryBoard to run (ex: -sb storyboard_QA_rest.json -sb "/qa/tests/sb/sb01.json"), can be several
        -ilv        Include tests of level y  (v1.0.2)
        -elv        Exclude tests of level y  (v1.0.2)
        -alv        Include tests above level y  (v1.0.2)
        -blv        Include tests below level y  (v1.0.2)
        -if         Include tests by @FEATURES tag
        -ef         Exclude tests by @FEATURES tag
        -itn        Include tests by @TN tag (beginsWith) (v1.3.2)
        -etn        Exclude tests by @TN tag (beginsWith) (v1.3.2)
        

- ## Select Reporters
    #### options:
        -reporter   add Reporter (ex: -reporter echo -reporter log)
        -r          add Reporter (ex: -r echo -r log -r web -r slack -r excel -r portalio -r tpio -r junitxml)

    #### Reporters:
    * **Echo:** shows test execution on stdout, and errors in stderr
    * **ReportPortalIO:** Web REST DB and reporter, with 3 different projects:
    * **Log:** shows test execution on .log file, with the same name as the project_name, errors are shown in stderr
    * **Excel:** creates an Excel file with test execution summary and test execution details
    * **Slack:** tests results are sent to slack channel
    * **Web:** tests results can be seen in realtime on a browser
    * **TestProjectIO:** mostly dedicated for webpages tests (it replaces selenium)
    * **JUnitXML:** test results will be saved on report.xml file   (since v1.4.1)


- ## Run:
    #### options:
        -rid        Run ID (ex: -rid 17, if not passed than current hour and minute will be used ex: 2359)
        -pn         Project Name (ex: -pn jules)
        -env        Environment name to test (ex: -env dev)  (v1.0.4)
        -rf         Results Folder (ex: -rf "/qa/test_results/"), where the tests results will be stored
        -tf         Tests Folder (ex: -tf "/qa/tests_scripts/jules/"), full path to where the tests are
        -repeat     Run the exact same pipeline that amount of times
    
    #### flags
        --dryrun    All tests will run but without really being executed (all of them will end with SKIPPED)
        --debugcode Disables the try/except on tests so errors are shown
        --1         Override test definitions of how many times tests will run (ncycle)
    

- ## Mode of Operation:
    - #### Example of usage:
      ```
      python3 run.py -reporter log -reporter portalio -rid 1 -sb "/qa/testipy/sb/sb01.json" -et NO_RUN -it DEV
      ```
    - #### Storyboard:      
        - If storyboard passed, tests will run by the order defined on json file
        - If no storyboard is passed, then tests will run ordered (DESC) by package name, @PRIO defined on suite, then by @PRIO defined on test itself
    - #### Results Folder:
        - A folder will be created under the (specified -rf option) composed by: projectName_currentDate_RID (ex: testipy_20201231_00525)
        - Under the folder defined above, subfolders can be created with package_name/suite_name containing the tests results (created by each reporter)
    - #### Tests not ended:
        - If a test ends without being formally ended (by a testFailed, testSkipped or testPassed), it will be passed by the executor
            
