import time
import collections
import emen2.db
db = emen2.db.opendb(admin=True)

count_keys = {}
count_values = {}
count_time = {}

with db:
    txn = db._txn
    pds = db.paramdef.filter()
    for pd in pds:
        t = time.time()
        count_keys[pd] = 0
        count_values[pd] = 0
        try:
            ind = db._db.dbenv['record'].getindex(pd, txn=txn)
        except Exception, e:
            print "Error:", e
            ind = None
        if ind:
            for k,v in ind.items(txn=txn):
                count_keys[pd] += 1
                count_values[pd] += len(v)
        count_time[pd] = time.time() - t
        print "========="
        print pd
        print "keys:", count_keys[pd]
        print "values:", count_values[pd]
        print "time:", count_time[pd]
        
# unused = [u'vartype', u'publish', u'spot_alignment_2_deflectors', u'textual_descriptions', u'box_color', u'immutable', u'fax', u'condenser_stigmator_deflectors', u'domain_cryoem', u'iter', u'humidity', u'gun_shift_deflectors', u'rate', u'voltage_lens', u'delta_z', u'visualization_codec', u'person_image', u'current', u'blotting', u'ctf', u'trainer', u'private', u'absorbance', u'lens_voltage_projector', u'magnification', u'camera', u'biological_target', u'mainview', u'concentration_pf', u'phone', u'box_coords', u'fine_objective_lens', u'visualization_credits_funding', u'focus_centering', u'projector_lens', u'root', u'projector_deflectors', u'history', u'intermediate_stigmator_deflectors', u'comment_goals', u'hazard', u'biology_of_project', u'controlhint', u'purification', u'exposure_time', u'gun_tilt_deflectors', u'disabled', u'desc_short', u'group', u'visualization_resolution', u'file_volume_masks', u'equipment_service', u'condenser_tilt_deflectors', u'name', u'comments_creator', u'coarse_objective_lens', u'wavelength', u'camera_index', u'comment_postfreezing_grid', u'phone_fax_international', u'image_shift_1_deflectors', u'job_title', u'imaging', u'md5', u'descriptive_information', u'length', u'visualization_bitrate', u'ddd_raw_frame_suffix', u'symmetry', u'typicalchld', u'comment_grid', u'owner', u'size', u'publication', u'privacy', u'objective_mini_lens', u'filesize', u'temperature_tem_stage', u'concentration', u'condenser_mini_lens', u'angle', u'equipment', u'contact', u'condenser_lens_1', u'compress', u'filesize_compress', u'url', u'faraday_plate_peak', u'segmentation_amira_network', u'comment_analysis', u'observed_by', u'signupinfo', u'ratio', u'experimental-techniques', u'film_camera', u'freezing', u'ccd_camera', u'physical_property', u'microscopy', u'microscope', u'reference', u'md5_compress', u'delta_tx', u'condenser_lens_3', u'condenser_lens_2', u'filename', u'paramdef', u'tem_polepiece', u'comment_pretreatment_grid', u'defaultunits', u'maxres', u'aliquot', u'spot_alignment_1_deflectors', u'desc_long', u'choices', u'parameters_reconstruction', u'property', u'specimen_holder', u'comment_project_desc', u'comment_specimen_stability', u'vitrification', u'binary', u'views', u'camera_units', u'intermediate_lens_2', u'intermediate_lens_3', u'visualization_credits_pi', u'user', u'stack', u'identifiers', u'defocus', u'temperature', u'condenser_shift_deflectors', u'keytype', u'ddd_raw_frame_save_summed', u'dose', u'voltage', u'displayname', u'comments', u'indexed', u'grid', u'password', u'delta_ty', u'ddd_camera', u'dilution', u'stack_totaldose', u'chimera_session', u'ice', u'core', u'delta_x', u'delta_y', u'processing', u'phone_voice_international', u'comment_aliquot', u'sequence', u'volume', u'file_volume', u'record', u'comment_project_progress', u'scanner', u'binary_data', u'intermediate_lens_1', u'film', u'project_information', u'test', u'vitrobot', u'ccd_serialno', u'lens', u'stack_stagepos', u'structure', u'date_time', u'ddd_raw_frame_type', u'acquire_text', u'final_reconstruction', u'image_shift_2_deflectors', u'mass', u'date_submit', u'microscope_serialno', u'objective_stigmator_deflectors', u'microscope_demo']


# >>> [i[0] for i in db.rel.children(unused, keytype='paramdef').items() if len(i[1])==0] 
# [u'exposure_time', u'comment_analysis', u'observed_by', u'keytype',
# u'ddd_raw_frame_save_summed', u'disabled', u'signupinfo', u'vartype', u'comment_postfreezing_grid', u'spot_alignment_2_deflectors', u'person_image', u'desc_short',
# u'group', u'camera_units', u'visualization_resolution', u'file_volume_masks', u'delta_tx', u'fine_objective_lens', u'immutable', u'fax', u'displayname',
# u'comments', u'condenser_stigmator_deflectors', u'film_camera', u'test', u'comment_grid', u'domain_cryoem', u'password', u'delta_ty', u'condenser_tilt_deflectors',
# u'name', u'iter', u'vitrobot', u'box_color', u'visualization_bitrate', u'md5_compress', u'gun_shift_deflectors', u'lens_voltage_projector',
# u'coarse_objective_lens', u'wavelength', u'condenser_lens_1', u'condenser_lens_3', u'condenser_lens_2', u'tem_polepiece', u'stack_totaldose',
# u'visualization_codec', u'chimera_session', u'publish', u'filename', u'phone_fax_international', u'image_shift_1_deflectors', u'job_title', u'delta_x', u'delta_y',
# u'delta_z', u'stack_stagepos', u'md5', u'defaultunits', u'phone_voice_international', u'ddd_raw_frame_suffix', u'trainer', u'typicalchld', u'private',
# u'objective_stigmator_deflectors', u'maxres', u'owner', u'comment_aliquot', u'privacy', u'filesize', u'objective_mini_lens', u'mainview', u'phone',
# u'temperature_tem_stage', u'spot_alignment_1_deflectors', u'comment_project_desc', u'desc_long', u'comment_specimen_stability', u'choices',
# u'visualization_credits_funding', u'record', u'focus_centering', u'projector_lens', u'parameters_reconstruction', u'property', u'projector_deflectors', u'history',
# u'specimen_holder', u'concentration_pf', u'box_coords', u'comments_creator', u'comment_pretreatment_grid', u'intermediate_stigmator_deflectors',
# u'intermediate_lens_1', u'condenser_mini_lens', u'binary', u'faraday_plate_peak', u'defocus', u'views', u'gun_tilt_deflectors', u'intermediate_lens_2', u'indexed',
# u'intermediate_lens_3', u'comment_goals', u'ccd_serialno', u'paramdef', u'compress', u'visualization_credits_pi', u'date_submit', u'user', u'filesize_compress',
# u'ddd_raw_frame_type', u'controlhint', u'comment_project_progress', u'acquire_text', u'camera_index', u'contact', u'condenser_shift_deflectors',
# u'microscope_serialno', u'segmentation_amira_network', u'image_shift_2_deflectors']


