elifePipeline {
    node('containers-jenkins-plugin') {
        def isNew
        def candidateVersion
        def commit

        stage 'Checkout', { checkout scm
            commit = elifeGitRevision()
        }

        stage 'Build images', {
            checkout scm
            dockerComposeBuild(commit)
        }

        stage 'Check version', {
            candidateVersion = dockerComposeRunAndCaptureOutput(
                "sciencebeam",
                "./print_version.sh",
                commit
            ).trim()
            echo "Candidate version: ${candidateVersion}"
            isNew = sh(script: "git tag | grep v${candidateVersion}", returnStatus: true) != 0
            echo "isNew: ${isNew}"
        }

        stage 'Project tests', {
            try {
                sh "make IMAGE_TAG=${commit} ci-test"
            } finally {
                sh "make ci-clean"
            }
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
                if (isNew) {
                    def image = DockerImage.elifesciences(this, 'sciencebeam', commit)
                    image.tag('latest').push()
                    image.tag(candidateVersion).push()
                }
            }

            stage 'Tag release', {
                if (isNew) {
                    def releaseTag = "v${candidateVersion}"
                    echo "Release tag: ${releaseTag}"
                    sh "git tag ${releaseTag} && git push origin ${releaseTag}"
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
