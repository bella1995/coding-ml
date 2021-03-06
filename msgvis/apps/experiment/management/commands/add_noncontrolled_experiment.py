from django.core.management.base import BaseCommand, make_option, CommandError
import msgvis.apps.experiment.models as experiment_models
from msgvis.apps.base.utils import check_or_create_dir
from django.db import transaction

import logging
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Create a new non-controlled experiment."
    args = '<dictionary_id> <output_folder>'
    option_list = BaseCommand.option_list + (
        make_option('-u', '--users',
                    default=4,
                    dest='num_users',
                    help='Num of users under this experiment'
        ),
        make_option('-n', '--name',
                    default='Experiment',
                    dest='experiment_name',
                    help='Name of this experiment'
        ),

    )

    def handle(self, dictionary_id, output_folder, **options):

        if not dictionary_id:
            raise CommandError("Dictionary id is required.")
        try:
            dictionary_id = int(dictionary_id)
        except ValueError:
            raise CommandError("Dictionary id must be a number.")

        if not output_folder:
            raise CommandError("Output folder path is required.")

        num_users = options.get('num_users')
        experiment_name = options.get('experiment_name')

        # make sure the folder exists
        check_or_create_dir(output_folder)

        output_filename = "%s/user_accounts.log" % output_folder

        with open(output_filename, "w") as output:
            with transaction.atomic(savepoint=False):
                # create an experiment
                experiment = experiment_models.Experiment(name=experiment_name,
                                                          saved_path_root=output_folder,
                                                          dictionary_id=dictionary_id,
                                                          isControlled=False)
                experiment.save()

                experiment.initialize_noncontrolled_experiment(#num_conditions=num_conditions,
                                                 #num_stages=num_stages,
                                                 num_users=num_users,
                                                 output=output)


