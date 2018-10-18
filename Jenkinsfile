elifeLibrary {
    def isNew
    def candidateVersion
    def commit

    stage 'Checkout', {
        checkout scm
        commit = elifeGitRevision()
    }

    node('containers-jenkins-plugin') {
        stage 'Build images', {
            checkout scm
            dockerComposeBuild(commit)
            candidateVersion = dockerComposeRunAndCaptureOutput(
                "sciencebeam",
                "./print_version.sh",
                commit
            ).trim()
            echo "Candidate version: v${candidateVersion}"
        }

        stage 'Project tests', {
            dockerComposeRun(
                "sciencebeam",
                "./project_tests.sh",
                commit
            )
        }

        elifeMainlineOnly {
            stage 'Merge to master', {
                elifeGitMoveToBranch commit, 'master'
            }

            stage 'Push unstable image', {
                def image = DockerImage.elifesciences(this, 'sciencebeam', commit)
                def unstable_image = image.addSuffixAndTag('_unstable', commit)
                unstable_image.tag('latest').push()
                unstable_image.push()
            }

            stage 'Push release image', {
                isNew = sh(script: "git tag | grep v${candidateVersion}", returnStatus: true) != 0
                if (isNew) {
                    def image = DockerImage.elifesciences(this, 'sciencebeam', commit)
                    image.tag('latest').push()
                    image.tag(candidateVersion).push()
                }
            }

            stage 'Downstream', {
                if (isNew) {
                    build job: '/dependencies/dependencies-sciencebeam-texture-update-sciencebeam', wait: false, parameters: [string(name: 'tag', value: candidateVersion)]
                }
            }
        }
    }
}
