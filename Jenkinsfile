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
    }

    elifeMainlineOnly {
        stage 'Merge to master', {
            elifeGitMoveToBranch commit, 'master'
        }

        stage 'Push image', {
            def image = DockerImage.elifesciences(this, 'sciencebeam', commit)
            image.push()
            image.tag('latest').push()
        }

        stage 'Downstream', {
            build job: '/dependencies/dependencies-sciencebeam-texture-update-sciencebeam', wait: false, parameters: [string(name: 'commit', value: commit)]
        }
    }
}
