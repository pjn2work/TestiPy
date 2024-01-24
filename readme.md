
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
        -ilv        Include tests of level y
        -elv        Exclude tests of level y
        -alv        Include tests above level y
        -blv        Include tests below level y
        -if         Include tests by @FEATURES tag
        -ef         Exclude tests by @FEATURES tag
        -itn        Include tests by @TN tag (beginsWith)
        -etn        Exclude tests by @TN tag (beginsWith)
        

- ## Select Reporters
    #### options:
        -reporter   add Reporter (ex: -reporter echo -reporter log)
        -r          add Reporter (ex: -r echo -r log -r web -r slack -r excel -r portalio -r tpio -r junitxml)

    #### Reporters:
    * **echo:** shows test execution on stdout, and errors in stderr
    * **excel:** creates an Excel file with test execution summary and test execution details
    * **log:** shows test execution on .log file, with the same name as the project_name, errors are shown in stderr
    * **portalio:** ReportPortalIO Web REST DB and reporter:
    * **slack:** tests results are sent to Slack channel
    * **web:** tests results can be seen in realtime on a browser
    * **xml:** test results will be saved on report.xml file


- ## Run:
    #### options:
        -rid        Run ID (ex: -rid 17, if not passed than current hour and minute will be used ex: 2359)
        -pn         Project Name (ex: -pn jules)
        -env        Environment name to test (ex: -env dev)
        -rf         Results Folder (ex: -rf "/qa/test_results/"), where the tests results will be stored
        -tf         Tests Folder (ex: -tf "/qa/tests_scripts/jules/"), full path to where the tests are
        -repeat     Run the exact same pipeline that amount of times
        -st         Suite Threads = 1..8 (ex: -st 4, meaning 4 suites can run in parallel) 
    
    #### flags
        --dryrun         All tests will run but without really being executed (all of them will end with SKIPPED)
        --debugcode      Disables the try/except on tests so errors are shown
        --debug-testipy  will show the stacktrace for testipy classes
        --1              Override test definitions of how many times tests will run (ncycle)
        --prof           Create file .prof with profiling data
    

- ## Mode of Operation:
    - #### Example of usage:
      ```
      python3 run.py -reporter log -reporter echo -rid 1 -tf "/home/testipy/my_test_scripts" -et NO_RUN -it DEV
      ```
    - #### Storyboard:      
        - If storyboard passed, tests will run by the order defined on json file
        - If no storyboard is passed, then tests will run ordered (DESC) by package name, @PRIO defined on suite, then by @PRIO defined on test itself
    - #### Results Folder:
        - A folder will be created under the (specified -rf option) composed by: projectName_currentDate_RID (ex: testipy_20201231_00525)
        - Under the folder defined above, subfolders can be created with package_name/suite_name containing the tests results (created by each reporter)
    - #### Tests not ended:
        - If a test ends without being formally ended (by a testFailed, testSkipped or testPassed), it will be passed by the executor
            
