# sql.sh
# psql queries

psql --username dx --dbname clarityDB -o step_stats.txt --no-align --field-separator $'\t' --command "
SELECT
    project.name as project,
    sample.name as sample,
    labprotocol.protocolname as protcol,
    processtype.displayname as step,
    project.createddate as import_date,
    process.createddate as step_start,
    process.lastmodifieddate as step_end,
    process.lastmodifieddate - process.createddate as step_duration,
    process.lastmodifieddate - project.createddate as total_duration
FROM project
INNER JOIN sample ON project.projectid = sample.projectid
INNER JOIN artifact_sample_map ON sample.processid = artifact_sample_map.processid
INNER JOIN artifact ON artifact_sample_map.artifactid = artifact.artifactid
INNER JOIN (
    SELECT DISTINCT processid, inputartifactid
    FROM processiotracker
    ) pt
    ON artifact.artifactid = pt.inputartifactid
INNER JOIN process on pt.processid = process.processid
INNER JOIN processtype on process.typeid = processtype.typeid
INNER JOIN protocolstep on process.protocolstepid = protocolstep.stepid
INNER JOIN labprotocol on protocolstep.protocolid = labprotocol.protocolid
WHERE project.name LIKE 'Dx%'
ORDER BY import_date, sample, process.processid;
"

psql --username dx --dbname clarityDB -o protcol_stats.txt --no-align --field-separator $'\t' --command "
SELECT
    project.name as project,
    sample.name as sample,
    labprotocol.protocolname as protcol,
    MIN(project.createddate) as import_date,
    MIN(process.createddate) as protcol_start,
    MAX(process.lastmodifieddate) as protcol_end,
    MAX(process.lastmodifieddate)- MIN(process.createddate) as protcol_duration,
    MAX(process.lastmodifieddate) - MIN(project.createddate) as total_duration
FROM project
INNER JOIN sample ON project.projectid = sample.projectid
INNER JOIN artifact_sample_map ON sample.processid = artifact_sample_map.processid
INNER JOIN artifact ON artifact_sample_map.artifactid = artifact.artifactid
INNER JOIN (
    SELECT DISTINCT processid, inputartifactid
    FROM processiotracker
    ) pt
    ON artifact.artifactid = pt.inputartifactid
INNER JOIN process on pt.processid = process.processid
INNER JOIN processtype on process.typeid = processtype.typeid
INNER JOIN protocolstep on process.protocolstepid = protocolstep.stepid
INNER JOIN labprotocol on protocolstep.protocolid = labprotocol.protocolid
WHERE project.name LIKE 'Dx%'
GROUP BY project.name, sample.name, labprotocol.protocolname
ORDER BY import_date, sample, total_duration;
"

psql --username dx --dbname clarityDB -o sample_stats.txt --no-align --field-separator $'\t' --command "
SELECT
    project.name as project,
    sample.name as sample,
    MIN(project.createddate) as import_date,
    MIN(process.createddate) as workflow_start,
    MAX(process.lastmodifieddate) as workflow_end,
    MAX(process.lastmodifieddate)- MIN(process.createddate) as workflow_duration,
    MAX(process.lastmodifieddate) - MIN(project.createddate) as total_duration
FROM project
INNER JOIN sample ON project.projectid = sample.projectid
INNER JOIN artifact_sample_map ON sample.processid = artifact_sample_map.processid
INNER JOIN artifact ON artifact_sample_map.artifactid = artifact.artifactid
INNER JOIN (
    SELECT DISTINCT processid, inputartifactid
    FROM processiotracker
    ) pt
    ON artifact.artifactid = pt.inputartifactid
INNER JOIN process on pt.processid = process.processid
INNER JOIN processtype on process.typeid = processtype.typeid
INNER JOIN protocolstep on process.protocolstepid = protocolstep.stepid
INNER JOIN labprotocol on protocolstep.protocolid = labprotocol.protocolid
WHERE project.name LIKE 'Dx%'
GROUP BY project.name, sample.name
ORDER BY import_date, sample;
"
