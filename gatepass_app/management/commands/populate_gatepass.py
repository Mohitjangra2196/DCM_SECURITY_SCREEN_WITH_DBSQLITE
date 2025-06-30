# gatepass_app/management/commands/populate_gatepass.py
from django.core.management.base import BaseCommand
from gatepass_app.models import GatePass
import datetime

class Command(BaseCommand):
    help = 'Deletes all old records and populates the GatePass table with new sample data.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Deleting all existing GatePass records...'))
        try:
            # Delete all existing records
            deleted_count, _ = GatePass.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'Successfully deleted {deleted_count} old GatePass records.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error deleting old records: {e}'))
            return # Exit if deletion fails

        self.stdout.write(self.style.SUCCESS('Starting to populate GatePass data...'))

        gatepass_data = [
            {
                'GATEPASS_NO': '0001',
                'GATEPASS_DATE': datetime.date(2025, 6, 28),
                'PAYCODE': 'EMP001',
                'NAME': 'Rahul Sharma',
                'DEPARTMENT': 'IT',
                'GATEPASS_TYPE': 'Offical',
                'REMARKS': 'Laptop for repair',
                'REQUEST_TIME': '10:00 AM',
                'AUTH': 'YES',
                'AUTH1_BY': 'Manager A',
                'AUTH1_STATUS': 'ByPass',
                'AUTH1_DATE': datetime.date(2025, 6, 28),
                'AUTH1_REMARKS': 'Approved by HOD',
                'FINAL_STATUS': 'A',
                'OUT_TIME': datetime.datetime(2025, 6, 28, 10, 30, 0),
                'OUT_BY': 'Guard_X',
                'IN_TIME': None,
                'IN_BY': None,
                'INOUT_STATUS': 'O',
                'UNIT_NAME': 'UNIT-1',  # New field value
                'EMP_TYPE': 'STAFF',    # New field value
                'LUNCH': 'Y',           # New field value
            },
            {
                'GATEPASS_NO': '0002',
                'GATEPASS_DATE': datetime.date(2025, 6, 27),
                'PAYCODE': 'EMP002',
                'NAME': 'Priya Singh',
                'DEPARTMENT': 'HR',
                'GATEPASS_TYPE': 'Offical',
                'REMARKS': 'Documents for verification',
                'REQUEST_TIME': '09:15 AM',
                'AUTH': '1',
                'AUTH1_BY': 'Manager B',
                'AUTH1_STATUS': 'ByPass',
                'AUTH1_DATE': datetime.date(2025, 6, 27),
                'AUTH1_REMARKS': 'Approved',
                'FINAL_STATUS': 'A',
                'OUT_TIME': None,
                'OUT_BY': None,
                'IN_TIME': None,
                'IN_BY': None,
                'INOUT_STATUS': None,
                'UNIT_NAME': 'UNIT-2',  # New field value
                'EMP_TYPE': 'WORKER',   # New field value
                'LUNCH': 'N',           # New field value
            },
            {
                'GATEPASS_NO': '0003', # Adding a third entry for variety
                'GATEPASS_DATE': datetime.date(2025, 6, 29),
                'PAYCODE': 'EMP003',
                'NAME': 'Amit Kumar',
                'DEPARTMENT': 'Sales',
                'GATEPASS_TYPE': 'Personal',
                'REMARKS': 'Client meeting',
                'REQUEST_TIME': '11:00 AM',
                'AUTH': 'Y',
                'AUTH1_BY': 'Manager C',
                'AUTH1_STATUS': 'Approved',
                'AUTH1_DATE': datetime.date(2025, 6, 29),
                'AUTH1_REMARKS': 'Meeting confirmed',
                'FINAL_STATUS': 'A',
                'OUT_TIME': None,
                'OUT_BY': None,
                'IN_TIME': None,
                'IN_BY': None,
                'INOUT_STATUS': None,
                'UNIT_NAME': 'UNIT-1',
                'EMP_TYPE': 'STAFF',
                'LUNCH': 'Y',
            },
        ]

        try:
            for data in gatepass_data:
                GatePass.objects.create(**data)
            self.stdout.write(self.style.SUCCESS(f'Successfully populated {len(gatepass_data)} new GatePass records.'))

            # Verify entries (optional)
            self.stdout.write(self.style.SUCCESS('\nVerifying entries:'))
            all_gatepasses = GatePass.objects.all()
            for gp in all_gatepasses:
                # Include new fields in print for verification
                self.stdout.write(f"  Gatepass No: {gp.GATEPASS_NO}, Name: {gp.NAME}, Dept: {gp.DEPARTMENT}, Unit: {gp.UNIT_NAME}, EmpType: {gp.EMP_TYPE}, Lunch: {gp.LUNCH}, Status: {gp.FINAL_STATUS}, IN/OUT: {gp.INOUT_STATUS}")

            self.stdout.write(self.style.SUCCESS('\nGatePass data population complete!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred during data population: {e}'))