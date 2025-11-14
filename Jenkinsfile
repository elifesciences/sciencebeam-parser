// import groovy.json.JsonSlurper

// @NonCPS
// def jsonToPypirc(String jsonText, String sectionName) {
//     def credentials = new JsonSlurper().parseText(jsonText)
//     echo "Username: ${credentials.username}"
//     return "[${sectionName}]\nusername: ${credentials.username}\npassword: ${credentials.password}"
// }

// def withPypiCredentials(String env, String sectionName, doSomething) {
//     try {
//         writeFile(file: '.pypirc', text: jsonToPypirc(sh(
//             script: "vault.sh kv get -format=json secret/containers/pypi/${env} | jq .data.data",
//             returnStdout: true
//         ).trim(), sectionName))
//         doSomething()
//     } finally {
//         sh 'echo > .pypirc'
//     }
// }


// elifePipeline {
//     node('containers-jenkins-plugin') {
//         def commit
//         def version

//         stage 'Checkout', {
//             checkout scm
//             commit = elifeGitRevision()
//             if (env.TAG_NAME) {
//                 version = env.TAG_NAME - 'v'
//             } else {
//                 version = 'develop'
//             }
//         }

//         stage 'Build and run tests', {
//             try {
//                 withCommitStatus({
//                     sh "make IMAGE_TAG=${commit} REVISION=${commit} ci-build-all"
//                 }, 'ci-build-all', commit)
//                 withCommitStatus({
//                     sh "make IMAGE_TAG=${commit} REVISION=${commit} ci-lint"
//                 }, 'ci-lint', commit)
//                 withCommitStatus({
//                     sh "make IMAGE_TAG=${commit} REVISION=${commit} ci-pytest"
//                 }, 'ci-pytest', commit)
//                 withCommitStatus({
//                     sh "make IMAGE_TAG=${commit} REVISION=${commit} ci-end-to-end"
//                 }, 'ci-end-to-end', commit)
//             } finally {
//                 sh "make ci-clean"
//             }
//         }

//         elifeMainlineOnly {
//             stage 'Merge to master', {
//                 elifeGitMoveToBranch commit, 'master'
//             }

//             stage 'Push unstable sciencebeam-parser image', {
//                 def image = DockerImage.elifesciences(this, 'sciencebeam-parser', commit)
//                 def unstable_image = image.addSuffixAndTag('_unstable', commit)
//                 unstable_image.tag('latest').push()
//                 unstable_image.push()
//             }

//             stage 'Push unstable sciencebeam-parser cv image', {
//                 def tag = "${commit}-cv"
//                 def image = DockerImage.elifesciences(this, 'sciencebeam-parser', tag)
//                 def unstable_image = image.addSuffixAndTag('_unstable', tag)
//                 unstable_image.tag('latest-cv').push()
//                 unstable_image.push()
//             }
//         }

//         elifePullRequestOnly { prNumber ->
//             stage 'Push package to test.pypi.org', {
//                 withPypiCredentials 'staging', 'testpypi', {
//                     sh "make IMAGE_TAG=${commit} REVISION=${commit} ci-push-testpypi"
//                 }
//             }
//         }

//         elifeTagOnly { repoTag ->
//             stage 'Push stable sciencebeam-parser image', {
//                 def image = DockerImage.elifesciences(this, 'sciencebeam-parser', commit)
//                 image.tag('latest').push()
//                 image.tag(version).push()
//             }

//             stage 'Push stable sciencebeam-parser cv image', {
//                 def tag = "${commit}-cv"
//                 def image = DockerImage.elifesciences(this, 'sciencebeam-parser', tag)
//                 image.tag('latest-cv').push()
//                 image.tag("${version}-cv").push()
//             }

//             stage 'Push package to pypi', {
//                 withPypiCredentials 'prod', 'pypi', {
//                     sh "make IMAGE_TAG=${commit} VERSION=${version} NO_BUILD=y ci-push-pypi"
//                 }
//             }
//         }
//     }
// }
