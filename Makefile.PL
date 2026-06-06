use strict;
use warnings;
use ExtUtils::MakeMaker;

my $version = do {
    open my $fh, '<', 'VERSION' or die "Cannot open VERSION: $!";
    my $v = <$fh>;
    close $fh;
    $v =~ s/\s+\z//;
    $v;
};

WriteMakefile(
    NAME             => 'App::Sanoid',
    ABSTRACT         => 'Policy-driven ZFS snapshot management and replication tools',
    VERSION          => $version,
    AUTHOR           => 'Jim Salter <jim@openoid.net>',
    LICENSE          => 'gpl_3',
    MIN_PERL_VERSION => '5.010',
    EXE_FILES        => [qw(sanoid syncoid findoid sleepymutex)],
    PREREQ_PM        => {
        'Config::IniFiles' => 0,
        'Capture::Tiny'    => 0,
    },
    META_MERGE => {
        'meta-spec' => { version => 2 },
        resources   => {
            homepage   => 'https://github.com/jimsalterjrs/sanoid',
            repository => {
                type => 'git',
                url  => 'https://github.com/jimsalterjrs/sanoid.git',
                web  => 'https://github.com/jimsalterjrs/sanoid',
            },
            bugtracker => {
                web => 'https://github.com/jimsalterjrs/sanoid/issues',
            },
        },
    },
);
